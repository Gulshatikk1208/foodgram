from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action

from rest_framework.permissions import (  # isort:skip
    SAFE_METHODS, AllowAny, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response  # isort:skip

from recipes.models import (  # isort:skip
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag
)
from users.models import Follow  # isort:skip

from . import filters, permissions, serializers, utils  # isort:skip
from .mixins import PatchModelMixin  # isort:skip
from .pagination import CustomPagePagination  # isort:skip


User = get_user_model()


class UserViewSet(
    PatchModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для операций с моделью User."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagePagination

    def get_queryset(self):
        """Возвращает разный queryset в зависимости от действия."""
        return (
            User.objects.filter(following__user=self.request.user)
            if self.action == 'subscriptions'
            else User.objects.all()
        )

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия."""
        if self.action == 'subscriptions':
            return serializers.SubscriptionSerializer
        if self.action == 'create':
            return serializers.UserCreateSerializer
        return serializers.UserSerializer

    def get_permissions(self):
        """Разрешает создание пользователя без аутентификации."""
        return (
            [AllowAny()]
            if self.action == 'create'
            else super().get_permissions()
        )

    @action(methods=['get'], detail=False)
    def me(self, request, *args, **kwargs):
        """Возвращает данные текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='set_password')
    def set_password(self, request):
        """Смена пароля."""
        serializer = serializers.SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'status': 'Пароль изменен'})

    @action(methods=['put'], detail=False, url_path='me/avatar')
    def set_avatar(self, request):
        """Устанавливает аватар."""
        serializer = serializers.AvatarSerializer(
            request.user,
            data={'avatar': request.data.get('avatar')},
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар."""
        if not request.user.avatar:
            return Response(
                {'detail': 'Аватар не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        """Возвращает список подписок текущего пользователя."""
        return self.list(request, *args, **kwargs)

    @action(methods=['post'], detail=True)
    def subscribe(self, request, *args, **kwargs):
        """Подписка на пользователя."""
        followed_user = get_object_or_404(User, id=self.kwargs.get('pk'))
        serializer = serializers.FollowSerializer(
            data={
                'user': request.user.id,
                'following': followed_user.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, *args, **kwargs):
        """Отписка от пользователя."""
        followed_user = get_object_or_404(User, id=self.kwargs.get('pk'))
        subscription = get_object_or_404(
            Follow,
            user=request.user,
            following=followed_user
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для операций с моделью Tag."""

    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для операций с моделью Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для операций с моделью Recipe."""

    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    pagination_class = CustomPagePagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.RecipeFilter

    def perform_create(self, serializer):
        """Автоматически назначает автора при создании рецепта."""
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от типа запроса."""
        return (
            serializers.RecipeSerializer
            if self.request.method in SAFE_METHODS
            else serializers.CreateRecipeSerializer
        )

    def get_permissions(self):
        """Выбирает разрешение в зависимотси от действия."""
        return (
            [permissions.IsAuthorOrReadOnlyPermission()]
            if self.action in ['update', 'partial_update', 'destroy']
            else super().get_permissions()
        )

    def _add_to_favorite_or_cart(self, request, serializer_class):
        """Метод для добавления в избранное и список покупок. """
        recipe = self.get_object()
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_favorite_or_cart(self, request, model):
        recipe = self.get_object()
        model_object = get_object_or_404(
            model,
            user=request.user,
            recipe=recipe
        )
        model_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True)
    def favorite(self, request, *args, **kwargs):
        """Добавление в избранное."""
        return self._add_to_favorite_or_cart(
            request, serializers.FavoriteSerializer
        )

    @favorite.mapping.delete
    def remove_from_favorite(self, request, *args, **kwargs):
        """Удаление из избранного."""
        return self._remove_from_favorite_or_cart(request, Favorite)

    @action(methods=['post'], detail=True)
    def shopping_cart(self, request, *args, **kwargs):
        """Добавление в список покупок."""
        return self._add_to_favorite_or_cart(
            request, serializers.CartSerializer
        )

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, *args, **kwargs):
        """Удаление из списка покупок."""
        return self._remove_from_favorite_or_cart(request, Cart)

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        """Загрузка списка покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__cart_related__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(amount=Sum('amount')).order_by('-amount')

        content = utils.generate_shopping_list_content(ingredients)

        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        if not recipe.short_link:
            recipe.short_link = utils.generate_unique_short_code()
            recipe.save(update_fields=['short_link'])
        short_url = request.build_absolute_uri(f'/s/{recipe.short_link}/')
        return Response(
            {'short-link': short_url},
            status=status.HTTP_200_OK
        )

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from users.models import Follow

from . import filters, permissions, serializers
from .pagination import CustomPagePagination

User = get_user_model()


class PartialUpdateModelMixin(UpdateModelMixin):
    """Миксин для реализации PATCH метода."""

    def partial_update(self, request, *args, **kwargs):
        """Частичное обновление экземпляра модели."""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class MyUserViewSet(PartialUpdateModelMixin,
                    mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    """Вьюсет для операций с моделью User."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagePagination

    def get_queryset(self):
        """Возвращает разный queryset в зависимости от действия."""
        if self.action == 'subscriptions':
            return User.objects.filter(following__user=self.request.user)
        return User.objects.all()

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия."""
        if self.action == 'subscriptions':
            return serializers.SubscriptionSerializer
        return serializers.UserSerializer

    @action(methods=['get'], detail=False)
    def me(self, request, *args, **kwargs):
        """Возвращает данные текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='set_password')
    def set_password(self, request):
        """Смена пароля."""
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response({'error': 'Неверный текущий пароль'}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({'status': 'Пароль изменен'})

    @action(methods=['put'], detail=False, url_path='me/avatar')
    def set_avatar(self, request):
        """Устанавливает аватар."""
        serializer = serializers.UserSerializer(
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
        """Управляет подпиской на пользователя."""
        followed_user = get_object_or_404(User, pk=self.kwargs.get('id'))
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
        followed_user = get_object_or_404(User, pk=self.kwargs.get('id'))
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
    permission_classes = [IsAuthenticatedOrReadOnly,
                          permissions.IsAuthorOrReadOnlyPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.RecipeFilter

    def perform_create(self, serializer):
        """Автоматически назначает автора при создании рецепта."""
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от типа запроса."""
        return (
            serializers.RecipeSerializer if self.request.method in SAFE_METHODS
            else serializers.CreateRecipeSerializer)

    @action(methods=['post'], detail=True)
    def favorite(self, request, *args, **kwargs):
        """Добавление в избранное."""
        recipe = self.get_object()
        serializer = serializers.FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def remove_from_favorite(self, request, *args, **kwargs):
        """Удаление из избранного."""
        recipe = self.get_object()
        favorite = get_object_or_404(
            Favorite,
            user=request.user,
            recipe=recipe
        )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True)
    def shopping_cart(self, request, *args, **kwargs):
        """Добавление в список покупок."""
        recipe = self.get_object()
        serializer = serializers.CartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, *args, **kwargs):
        """Удаление из списка покупок."""
        recipe = self.get_object()
        cart_item = get_object_or_404(
            Cart,
            user=request.user,
            recipe=recipe
        )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        """Загрузка списка покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(amount=Sum('amount')).order_by('-amount')

        content = self._generate_shopping_list_content(ingredients)

        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def _generate_shopping_list_content(self, ingredients):
        """Формирует содержимое списка покупок."""
        if not ingredients:
            return 'Список покупок пуст'

        content = "Список покупок:\n\n" + '\n'.join(
            f'{i+1}. {ing["ingredient__name"]} - '
            f'{ing["amount"]} {ing["ingredient__measurement_unit"]}'
            for i, ing in enumerate(ingredients)
        )
        return content

    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_link = request.build_absolute_uri(f"/s/{recipe.id}/")
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

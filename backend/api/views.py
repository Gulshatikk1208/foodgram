from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from users.models import Follow, User

from . import filters, permissions, serializers
from .pagination import CustomPagePagination


class BaseActionViewSetMixin:
    """Миксин для общих действий с рецептами."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_recipe(self):
        """Возвращает рецепт по id из URL."""
        return get_object_or_404(Recipe, id=self.kwargs.get('pk'))

    def handle_recipe_action(self, request, model, serializer_class):
        """Управляет действиями с рецептами."""
        recipe = self.get_recipe()

        if request.method == 'POST':
            if model.objects.filter(user=request.user, recipe=recipe).exists():
                raise ValidationError({'errors': 'Рецепт уже добавлен'},
                                      status=status.HTTP_400_BAD_REQUEST)

            serializer = serializer_class(
                data={'user': request.user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        model.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):
    """Вьюсет для операций с моделью User."""

    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagePagination

    @action(methods=['get'], detail=False)
    def me(self, request, *args, **kwargs):
        """Bозвращает данные текущего пользователя."""
        return super().me(request, *args, **kwargs)

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar')
    def avatar(self, request):
        """Устанавливает/удаляет аватар."""
        if request.method == 'PUT':
            serializer = serializers.CustomUserSerializer(
                request.user,
                data={'avatar': request.data.get('avatar')},
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        """Возвращает список подписок текущего пользователя."""
        serializer = serializers.SubscriptionSerializer(
            self.paginate_queryset(
                User.objects
                .filter(following__user=request.user)
            ),
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, *args, **kwargs):
        """Управляет подпиской/отпиской от пользователя."""
        followed_user = get_object_or_404(User, pk=self.kwargs.get('id'))

        if request.user == followed_user:
            raise ValidationError(
                {'Ошибка': 'Вы не можете подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Follow.objects.filter(user=request.user,
                                     following=followed_user).exists():
                raise ValidationError(
                    {'Ошибка': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
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

        Follow.objects.filter(
            user=request.user, following=followed_user
        ).delete()
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


class RecipeViewSet(BaseActionViewSetMixin, viewsets.ModelViewSet):
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

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, *args, **kwargs):
        """Добавление/удаление из избранного."""
        return self.handle_recipe_action(
            request, Favorite, serializers.FavoriteSerializer
        )

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, *args, **kwargs):
        """Добавление/удаление из списка покупок."""
        return self.handle_recipe_action(
            request, Cart, serializers.CartSerializer
        )

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        """Загрузка списка покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(amount=Sum('amount')).order_by('-amount')

        if not ingredients:
            return Response(
                {'message': 'Список покупок пуст'},
                status=status.HTTP_200_OK
            )

        content = (
            "Список покупок:\n\n" + '\n'.join(
                f'{i+1}. {ing["ingredient__name"]} - '
                f'{ing["amount"]} {ing["ingredient__measurement_unit"]}'
                for i, ing in enumerate(ingredients)
            )
        )

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
        recipe = self.get_recipe()
        short_link = request.build_absolute_uri(f"/s/{recipe.id}")
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

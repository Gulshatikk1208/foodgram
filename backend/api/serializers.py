import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer as UserCreate
from djoser.serializers import UserSerializer as UserDetail
from rest_framework import serializers

from foodgram_backend import constants
from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from users.models import Follow

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserCreateSerializer(UserCreate):
    """Сериализатор создания пользователя."""

    class Meta(UserCreate.Meta):
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class UserSerializer(UserDetail):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на другого."""
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and request.user.follower.filter(following=obj).exists()
        )


class SubscriptionRecipeSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецептов для подписок."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserSerializer):
    """Сериализатор подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя."""
        request = self.context['request']
        recipes_limit = constants.RECIPES_LIMIT
        try:
            recipes_limit_param = request.query_params.get('recipes_limit')
            if recipes_limit_param:
                limit = int(recipes_limit_param)
                if limit > 0:
                    recipes_limit = limit
        except (ValueError, TypeError):
            pass

        recipes = obj.recipes.all()[:recipes_limit]
        return SubscriptionRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов пользователя."""
        return obj.recipes.all().count()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/проверки подписок."""

    class Meta:
        model = Follow
        fields = ('user', 'following')
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message=('Подписка уже оформлена')
            ),
        )

    def validate(self, data):
        """Запрещает подписку на себя."""
        if data.get('user') == data.get('following'):
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на себя'})
        return data

    def to_representation(self, instance):
        """Возвращает данные о подписке."""
        return SubscriptionSerializer(
            instance=instance.following,
            context={'request': self.context.get('request')}
        ).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта."""

    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        read_only=True, many=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and obj.favorite_related.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину."""
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and obj.cart_related.filter(user=request.user).exists()
        )


class CreateRecipeIngredientSerializer(RecipeIngredientSerializer):
    """Сериализатор для ингредиентов при создании рецепта."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта."""

    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = CreateRecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def add_ingredients(self, ingredients, model):
        """Добавляет ингредиенты к рецепту."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=model,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        """Создает рецепт."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        self.add_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        RecipeIngredient.objects.filter(recipe=instance).delete()
        instance.tags.clear()

        super().update(instance, validated_data)
        self.add_ingredients(ingredients, instance)
        instance.tags.set(tags)
        return instance

    def to_representation(self, instance):
        """Возвращает рецепт после создания."""
        return RecipeSerializer(
            instance=instance,
            context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в избранное."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, attrs):
        if Favorite.objects.filter(**attrs).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return attrs

    def to_representation(self, instance):
        """Возвращает упрощенные данные рецепта."""
        return SubscriptionRecipeSerializer(
            instance=instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в корзину."""

    class Meta:
        model = Cart
        fields = ('user', 'recipe')

    def validate(self, attrs):
        if Cart.objects.filter(**attrs).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в список покупок.'
            )
        return attrs

    def to_representation(self, instance):
        """Возвращает упрощенные данные рецепта."""
        return SubscriptionRecipeSerializer(
            instance=instance.recipe,
            context={'request': self.context.get('request')}
        ).data

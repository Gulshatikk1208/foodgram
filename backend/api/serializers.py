from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import serializers
from users.models import Follow, User


class CustomUserCreateSerializer(UserCreateSerializer):
    """Кастомный сериализатор создания пользователя."""

    username = serializers.RegexField(regex=r'^[\w.@+-]+$', max_length=150)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class CustomUserSerializer(UserSerializer):
    """Кастомный сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False)

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
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, following=obj.id).exists()

    def update(self, instance, validated_data):
        """Изменяет аватар."""
        avatar = validated_data.pop('avatar', serializers.empty)
        user = super().update(instance, validated_data)
        if avatar is not serializers.empty:
            user.avatar = avatar
            user.save(update_fields=['avatar'])
        return user


class SubscrRecipeSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецептов для подписок."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(CustomUserSerializer):
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
        recipes_limit = request.query_params.get('recipes_limit', 6)
        recipes = obj.recipes.all()[:int(recipes_limit)]
        return SubscrRecipeSerializer(recipes, many=True).data

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

    def create(self, validated_data):
        """Создает подписку."""
        return Follow.objects.create(**validated_data)

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
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта."""

    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        read_only=True, many=True, source='recipe_ingredients')
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
        if not request or request.user.is_anonymous:
            return False
        return obj.favorited.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Cart.objects.filter(
            recipe=obj, user=request.user).exists()


class CreateRecipeIngredientSerializer(RecipeIngredientSerializer):
    """Сериализатор для ингредиентов при создании рецепта."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

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

    def to_representation(self, instance):
        """Возвращает рецепт после создания."""
        return RecipeSerializer(
            instance=instance,
            context={'request': self.context.get('request')}
        ).data

    def add_tags_ingredients(self, ingredients, tags, model):
        """Добавляет теги и ингредиенты к рецепту."""
        ingredients_for_recipe = []
        for ingredient in ingredients:
            ingredients_for_recipe.append(RecipeIngredient(
                recipe=model,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ))
        RecipeIngredient.objects.bulk_create(ingredients_for_recipe)

        model.tags.set(tags)

    def create(self, validated_data):
        """Создает рецепт с тегами и ингредиентами."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        self.add_tags_ingredients(ingredients, tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        instance.tags.clear()
        self.add_tags_ingredients(ingredients, tags, instance)
        return super().update(instance, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в избранное."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        """Возвращает упрощенные данные рецепта."""
        return SubscrRecipeSerializer(
            instance=instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в корзину."""

    class Meta:
        model = Cart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        """Возвращает упрощенные данные рецепта."""
        return SubscrRecipeSerializer(
            instance=instance.recipe,
            context={'request': self.context.get('request')}
        ).data

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from foodgram_backend import constants

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        verbose_name='Название тега',
        unique=True,
        max_length=constants.TAG_LENGTH
    )
    slug = models.SlugField(unique=True, max_length=constants.TAG_LENGTH)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(verbose_name='Название продукта')
    measurement_unit = models.CharField(verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=constants.RECIPE_MAX_LENGTH,
        verbose_name='Название блюда'
    )
    text = models.TextField(verbose_name='Описание рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (минуты)',
        validators=[
            MinValueValidator(1, 'Время приготовления должно быть больше 0.')
        ]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тег для рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes'
    )
    image = models.ImageField(
        upload_to='recipes/images',
        verbose_name='Изображение'
    )
    short_link = models.CharField(
        verbose_name='Сокращенная ссылка',
        max_length=constants.SHORT_LINK_MAX_LENGTH,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(1, 'Количество должно быть больше 0.')
        ]
    )

    class Meta:
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} - {self.amount}'
            f'{self.ingredient.measurement_unit}'
        )


class FavoriteCartBase(models.Model):
    """Абстрактная модель для избранного и списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name="%(class)s_related"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name="%(class)s_related"
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Favorite(FavoriteCartBase):
    """Модель избранного."""

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'


class Cart(FavoriteCartBase):
    """Модель списка покупок."""

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'

from django.contrib import admin

from foodgram_backend import constants

from .models import Cart, Favorite, Ingredient, Recipe, RecipeIngredient, Tag


class IngredientInline(admin.StackedInline):
    model = RecipeIngredient
    extra = constants.EXTRA_INGREDIENT_FORM
    min_num = constants.MIN_INGREDIENTS_PER_RECIPE
    validate_min = True


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientInline,)
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name', 'author__username')
    filter_horizontal = ('tags',)
    readonly_fields = ('favorite_counter',)

    fieldsets = (
        (None, {
            'fields': (
                'author',
                'name',
                'tags',
                'cooking_time',
                'text',
                'image',
                'favorite_counter'
            )
        }),
    )

    @admin.display(description='Добавлено в избранное (раз):')
    def favorite_counter(self, obj):
        return obj.favorite_related.all().count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')

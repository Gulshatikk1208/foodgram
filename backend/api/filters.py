import django_filters
from django_filters import filters
from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.CharFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.CharFilter(method='filter_by_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует по избранному."""
        if value != '1' or self.request.user.is_anonymous:
            return queryset
        return queryset.filter(favorited__user_id=self.request.user.id)

    def filter_by_cart(self, queryset, name, value):
        """Фильтрует по списку покупок."""
        if value != '1' or self.request.user.is_anonymous:
            return queryset
        return queryset.filter(cart__user_id=self.request.user.id)

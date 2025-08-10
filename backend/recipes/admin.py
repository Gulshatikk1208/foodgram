from django.contrib import admin

from .models import Cart, Favorite, Ingredient, Recipe, Tag


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_counter')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username')
    filter_horizontal = ('tags',)

    @admin.display(description='В избранном')
    def favorite_counter(self, obj):
        return obj.favorited.all().count()


class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Cart, CartAdmin)

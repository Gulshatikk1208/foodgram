from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect

from .models import Recipe


def redirect_to_recipe(request, short_code):
    """Редирект на полную ссылку рецепта."""
    print('Функция вызвана')
    try:
        recipe = Recipe.objects.get(short_link=short_code)
        print(f'Короткий код рецепта {recipe.id}: {recipe.short_link}')
        return HttpResponsePermanentRedirect(
            request.build_absolute_uri(f'/recipes/{recipe.id}')
        )
    except Recipe.DoesNotExist:
        print(f'Рецепт с кодом {recipe.short_link} не найден')
        return HttpResponseRedirect(request.build_absolute_uri('/not-found'))

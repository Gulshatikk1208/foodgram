from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect

from .models import Recipe


def redirect_to_recipe(request, short_code):
    """Редирект на полную ссылку рецепта."""
    try:
        recipe = Recipe.objects.get(short_link=short_code)
        return HttpResponsePermanentRedirect(f'/recipes/{recipe.id}/')
    except Recipe.DoesNotExist:
        return HttpResponseRedirect('/not-found')

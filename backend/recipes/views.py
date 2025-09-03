from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from .models import Recipe


def redirect_to_recipe(request, short_code):
    """Редирект на полную ссылку рецепта."""
    try:
        recipe = get_object_or_404(Recipe, short_link=short_code)
        return HttpResponsePermanentRedirect(
            request.build_absolute_uri(f'/recipes/{recipe.id}')
        )
    except Recipe.DoesNotExist:
        return HttpResponseRedirect(request.build_absolute_uri('/not-found'))

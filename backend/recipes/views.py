from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect

from .models import Recipe


def redirect_to_recipe(request, short_code):
    """Редирект на полную ссылку рецепта."""
    try:
        recipe = Recipe.objects.get(short_link=short_code)
        return HttpResponsePermanentRedirect(
            request.build_absolute_uri(f'/recipes/{recipe.id}/')
        )
    except Recipe.DoesNotExist:
        return HttpResponseRedirect(request.build_absolute_uri('/not-found'))

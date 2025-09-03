import logging

from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect

from .models import Recipe

logger = logging.getLogger(__name__)


def redirect_to_recipe(request, short_code):
    """Редирект на полную ссылку рецепта."""
    try:
        recipe = Recipe.objects.get(short_link=short_code)
        logger.info(f"Redirecting short link {short_code} to recipe {recipe.id}")
        return HttpResponsePermanentRedirect(
            request.build_absolute_uri(f'/recipes/{recipe.id}')
        )
    except Recipe.DoesNotExist:
        logger.warning(f"Short link {short_code} not found, redirecting to /not-found")
        return HttpResponseRedirect(request.build_absolute_uri('/not-found'))

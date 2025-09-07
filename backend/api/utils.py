import secrets
import string

from foodgram_backend import constants
from recipes.models import Recipe


def generate_unique_short_code(
    length=constants.SHORT_LINK_MAX_LENGTH
):
    """Генерирует уникальный короткий код для рецепта."""
    alphabet = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        if not Recipe.objects.filter(short_link=code).exists():
            return code


def generate_shopping_list_content(ingredients):
    """Формирует содержимое списка покупок."""
    if not ingredients:
        return 'Список покупок пуст'
    content = "Список покупок:\n\n" + '\n'.join(
        f'{i+1}. {ing["ingredient__name"]} - '
        f'{ing["amount"]} {ing["ingredient__measurement_unit"]}'
        for i, ing in enumerate(ingredients)
    )
    return content

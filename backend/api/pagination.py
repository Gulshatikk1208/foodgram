from rest_framework.pagination import PageNumberPagination

from backend.foodgram_backend import constants


class CustomPagePagination(PageNumberPagination):
    page_size = constants.PAGE_SIZE
    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_page_size = constants.PAGE_SIZE

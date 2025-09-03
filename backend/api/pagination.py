from rest_framework.pagination import PageNumberPagination

from foodgram_backend import constants


class CustomPagePagination(PageNumberPagination):
    page_size = constants.PAGE_SIZE
    page_query_param = constants.PAGE_QUERY_PARAM
    page_size_query_param = constants.PAGE_SIZE_QUERY_PARAM
    max_page_size = constants.PAGE_SIZE

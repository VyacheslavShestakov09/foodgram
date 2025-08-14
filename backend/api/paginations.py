from rest_framework.pagination import PageNumberPagination

PAGINATION_PAGE_SIZE = 6


class Pagination(PageNumberPagination):
    """Кастомная пагинация для API."""
    page_size = PAGINATION_PAGE_SIZE
    page_size_query_param = 'limit'

from django_filters import rest_framework as filters
from django.db.models import Q
from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов с поддержкой:
    - Фильтрации по тегам (slug)
    - Фильтрации по автору
    - Фильтрации по избранному
    - Фильтрации по списку покупок
    """
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты по избранному для текущего пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты по списку покупок текущего пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset


class IngredientSearchFilter(SearchFilter):
    """Кастомный фильтр для поиска ингредиентов.
    Поддерживает:
    - Поиск по началу названия (регистронезависимый)
    - Поиск по вхождению в любом месте названия
    """
    search_param = 'name'

    def get_search_terms(self, request):
        """Возвращает список терминов для поиска."""
        params = request.query_params.get(self.search_param, '')
        return params.replace(',', ' ').split()

    def filter_queryset(self, request, queryset, view):
        """Фильтрует queryset по поисковым терминам."""
        terms = self.get_search_terms(request)
        if not terms:
            return queryset
        return queryset.filter(
            Q(name__istartswith=terms[0])
            | Q(name__icontains=terms[0])
        ).order_by('name')

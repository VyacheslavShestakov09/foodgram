from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def recipe_short_redirect(request, short_code):
    """Перенаправление по короткой ссылке на рецепт"""
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return redirect(f'/api/recipes/{recipe.id}/')

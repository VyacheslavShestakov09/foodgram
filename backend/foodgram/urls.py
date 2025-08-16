from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet
from recipes.views import recipe_short_redirect

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router_v1.urls)),
    path('api/auth/', include('djoser.urls.authtoken')),
    path(
        'r/<str:short_code>/',
        recipe_short_redirect,
        name='recipe_short_redirect'
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

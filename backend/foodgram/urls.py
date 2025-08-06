from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter

from api.views import UserViewSet, TagViewSet, IngredientViewSet, RecipeViewSet

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router_v1.urls)),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/recipes/<int:pk>/get-link/',
         RecipeViewSet.as_view({'get': 'get_link'}),
         name='recipe-get-link'),
    path('api/users/<int:pk>/subscribe/',
         UserViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}),
         name='user-subscribe'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

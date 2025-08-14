from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response\

from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    Favorite,
    ShoppingCart,
    RecipeIngredient,
)
from api.serializers import (
    FavoriteSerializer,
    RecipeShortSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    UserSerializer,
    SubscriptionSerializer,
    SubscriptionCreateSerializer,
    AvatarUpdateSerializer,
)
from users.models import Subscription, User
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter, IngredientSearchFilter
from .paginations import Pagination


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для работы с пользователями.
    Наследуется от DjoserUserViewSet для стандартных действий:
    - Регистрация (POST /users/)
    - Получение списка пользователей (GET /users/)
    - Получение/обновление профиля (GET/PUT /users/{id}/)
    Добавлены кастомные действия:
    - set_password - изменение пароля
    - subscriptions - список подписок
    - subscribe - подписка/отписка
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = Pagination

    @action(
        ['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        """
        Переопределяем метод, чтобы ограничить запрос
        Указываем другое разрешение
        """
        return super().me(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        url_name='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        """Подписка на пользователя (POST)"""
        author = self.get_object()
        serializer = SubscriptionCreateSerializer(
            data={'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscriptionSerializer(
                author,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, *args, **kwargs):
        """Отписка от пользователя (DELETE)"""
        author = self.get_object()
        user = request.user
        deleted_count, _ = Subscription.objects.filter(
            user=user,
            author=author
        ).delete()
        if deleted_count == 0:
            return Response(
                {'Ошибка': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated]
            )
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        authors = User.objects.filter(
            subscribers__user=request.user
        ).order_by('first_name')
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['put', 'patch'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        """Обновление аватара текущего пользователя"""
        user = request.user
        serializer = AvatarUpdateSerializer(
            user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'avatar': user.avatar.url},
            status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара текущего пользователя"""
        user = request.user
        if user.avatar:
            user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для работы с тегами.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [IngredientSearchFilter]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами"""
    queryset = (
        Recipe.objects
        .select_related('author')
        .prefetch_related('tags', 'ingredients')
        .all()
        .order_by('-pub_date')
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = Pagination

    def get_serializer_class(self):
        """Определяет сериализатор в зависимости от типа запроса."""
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        recipe = self.get_object()
        serializer = FavoriteSerializer(
            data={
                'user': request.user.id,
                'recipe': recipe.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        recipe = self.get_object()
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'detail': 'Рецепт не найден в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в список покупок."""
        recipe = self.get_object()
        serializer = ShoppingCartSerializer(
            data={
                'user': request.user.id,
                'recipe': recipe.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        """Удаление рецепта из списка покупок."""
        recipe = self.get_object()
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if deleted_count == 0:
            return Response(
                {'detail': 'Рецепт не найден в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт"""
        recipe = self.get_object()
        if not recipe.short_code:
            recipe.short_code = recipe.generate_short_code()
            recipe.save(update_fields=['short_code'])
        return Response(
            {'short-link': request.build_absolute_uri(
                f'/r/{recipe.short_code}/'
            )},
            status=status.HTTP_200_OK)

    def _handle_relation_action(
            self,
            model,
            user,
            pk,
    ):
        """Обрабатывает добавление/удаление связей (избранное, покупки)."""
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if self.request.method == 'POST':
            if relation.exists():
                return Response(
                    {'detail': 'Рецепт уже добавлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if model == Favorite:
                serializer = FavoriteSerializer(
                    data={'user': user.id, 'recipe': recipe.id},
                    context={'request': self.request}
                )
            else:
                serializer = ShoppingCartSerializer(
                    data={'user': user.id, 'recipe': recipe.id},
                    context={'request': self.request}
                )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            recipe_serializer = RecipeShortSerializer(
                recipe,
                context={'request': self.request}
            )
            return Response(
                recipe_serializer.data,
                status=status.HTTP_201_CREATED
            )
        if not relation.exists():
            return Response(
                {'detail': 'Рецепт не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """
            Скачивание списка покупок текущего пользователя
            Создает текстовый файл со списком покупок.
        """
        recipes = Recipe.objects.filter(shopping_carts__user=request.user)
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total=Sum('amount')
        ).order_by('ingredient__name')

        if not ingredients.exists():
            return Response(
                {'detail': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )

        content = 'Список покупок:\n\n'
        for item in ingredients:
            content += (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) - "
                f"{item['total']}\n"
            )

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

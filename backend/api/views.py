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
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from recipes.models import (
    Recipe, Tag, Ingredient,
    Favorite, ShoppingCart, RecipeIngredient
)
from recipes.serializers import (
    FavoriteSerializer,
    RecipeShortSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
)

from users.models import Subscription, MyUser
from users.serializers import (
    UserSerializer,
    SubscriptionSerializer,
    AvatarUpdateSerializer
)
from .permissions import (
    IsAuthorOrReadOnly,
    IsAdminOrReadOnly,
)
from .filters import RecipeFilter, IngredientSearchFilter
from .paginations import CustomPagination


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
    queryset = MyUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_permissions(self):
        """Определяет права доступа в зависимости от действия."""
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        """Получение профиля текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe/',
        url_name='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        """Управление подписками на пользователей."""
        author_id = self.kwargs.get('pk')
        author = get_object_or_404(MyUser, id=author_id)
        user = request.user
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'Ошибка': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'Ошибка': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription = Subscription.objects.create(
                user=user,
                author=author
            )
            serializer = SubscriptionSerializer(
                subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = Subscription.objects.filter(user=user, author=author)
        if not subscription.exists():
            return Response(
                {'Ошибка': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated]
            )
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        queryset = Subscription.objects.filter(
            user=request.user
        ).order_by('author__first_name')
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['put', 'patch', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
        parser_classes=[JSONParser]
    )
    def avatar(self, request):
        """Управление аватаром текущего пользователя."""
        user = request.user
        if request.method in ('PUT', 'PATCH'):
            if 'avatar' not in request.data:
                return Response(
                    {'Ошибка': 'Файл аватара не найден'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = AvatarUpdateSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами (только чтение).
    Доступ:
    - Чтение: все пользователи
    - Изменение: только администраторы
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами.
    Доступ:
    - Чтение: все пользователи
    - Изменение: только администраторы
    Фильтрация:
    - Поиск по названию (регистронезависимый)
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [IngredientSearchFilter]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами.
    Доступ:
    - Создание: аутентифицированные пользователи
    - Изменение/удаление: только автор
    - Чтение: все пользователи
    Фильтрация:
    - По тегам (slug)
    - По автору
    - По наличию в избранном
    - По наличию в списке покупок
    """
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
    pagination_class = CustomPagination

    def get_serializer_class(self):
        """Определяет сериализатор в зависимости от типа запроса."""
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """Создает рецепт с текущим пользователем в качестве автора."""
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Управление избранными рецептами."""
        return self._handle_relation_action(
            Favorite,
            request.user,
            pk,
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Управление списком покупок.
        POST - добавить в список покупок
        DELETE - удалить из списка покупок
        """
        return self._handle_relation_action(
            ShoppingCart,
            request.user,
            pk,
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get_link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт"""
        recipe = self.get_object()
        return Response({
            'short-link': request.build_absolute_uri(
                f'/api/recipes/{recipe.id}/'
            )
        })

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
        recipes = Recipe.objects.filter(in_carts=request.user)
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

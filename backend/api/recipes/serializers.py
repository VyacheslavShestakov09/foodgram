from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from api.users.serializers import UserSerializer
from recipes.models import (
    Tag,
    Ingredient,
    RecipeIngredient,
    Recipe,
    Favorite,
    ShoppingCart
)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов"""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Чтение ингридиентов"""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Запись ингридиентов в рецепт"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор записи рецептов"""
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = RecipeIngredientWriteSerializer(many=True, required=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'ingredients',
            'name',
            'text',
            'cooking_time',
            'image'
        )

    def validate(self, data):
        """Проверяем что список ингредиентов не пустой,
        ингредиенты и теги не повторяются
        и время приготовления больше нуля
        """
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Укажте тэг! Поле обязательно'
            )
        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться!'
            )
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError('Заполните ингредиенты!')
        ingredient_ids = [item['id'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return data

    def validate_image(self, value):
        """Проверяем что изображение не пустое"""
        if not value:
            raise serializers.ValidationError(
                'Изображение обязательно для заполнения'
            )
        return value

    @staticmethod
    def do_ingredients(recipe, ingredients):
        """Получаем ингредиенты и их колличество"""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients
        ])

    def create(self, validated_data):
        """
        Создаёт новый рецепт с указанными тегами и ингредиентами.
        """
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            **validated_data)
        self.do_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        """
        Обновляет экземпляр рецепта, устанавливая новые теги и ингредиенты.
        Старые ингредиенты удаляются и заменяются новыми.
        """
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.do_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Преобразует рецепт в формат для чтения
        Использует RecipeReadSerializer для представления данных
        """
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов"""
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'tags',
            'ingredients',
            'name',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
            'image'
        )

    def get_ingredients(self, obj):
        """
        Возвращает список ингредиентов для указанного рецепта
        """
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientReadSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        """
        Проверяет, добавлен ли рецепт в избранное текущим пользователем.
        """
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """
        Проверяет, находится ли рецепт в списке покупок текущего пользователя.
        """
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )


class BaseUserRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для работы с рецептами пользователя"""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        fields = ('user', 'recipe')

    def validate(self, data):
        """
        Проверяет, что пользователь не добавляет свой рецепт
        в список покупок.
        """
        if data['user'] == data['recipe'].author:
            raise serializers.ValidationError(
                f'Нельзя добавить свой рецепт в'
                f'{self.Meta.model._meta.verbose_name}'
            )
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов с валидацией"""
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверка на добавление своего рецепта и дублирование"""
        if data['user'] == data['recipe'].author:
            raise serializers.ValidationError(
                'Нельзя добавить свой рецепт в избранное'
            )
        if Favorite.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже в избранном'
            )
        return data

    def to_representation(self, instance):
        """Преобразует вывод в краткий формат рецепта"""
        return RecipeShortSerializer(
            instance.recipe,
            context=self.context
        ).data


class ShoppingCartSerializer(BaseUserRecipeSerializer):
    """Сериализатор для списка покупок с валидацией"""
    class Meta(BaseUserRecipeSerializer.Meta):
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверка на добавление своего рецепта и дублирование"""
        if data['user'] == data['recipe'].author:
            raise serializers.ValidationError(
                'Нельзя добавить свой рецепт в список покупок'
            )
        if ShoppingCart.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже в списке покупок'
            )
        return data

    def to_representation(self, instance):
        """Преобразует вывод в краткий формат рецепта"""
        return RecipeShortSerializer(
            instance.recipe,
            context=self.context
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

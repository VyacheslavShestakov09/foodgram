from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from users.models import MyUser


User = get_user_model()


class Tag(models.Model):
    """Тэги для рецептов."""
    name = models.CharField(
        verbose_name='Тэг',
        unique=True,
        max_length=10,
    )
    slug = models.SlugField(
        verbose_name='Слаг тэга',
        unique=True,
        max_length=10
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return f'{self.name} - {self.slug}'


class Ingredient(models.Model):
    """Ингридиент для рецепта"""
    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=50
    )
    measurement_unit = models.CharField(
        max_length=50,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Recipe(models.Model):
    """Модель для рецепта"""
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=50,
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True,
        null=True,
        blank=True
    )
    image = models.ImageField(
        verbose_name='Изображение блюда',
        upload_to="recipe_images"
    )
    text = models.TextField(
        verbose_name='Описание блюда',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиент',
        through='RecipeIngredient'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэг',
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
    )
    in_favorites = models.ManyToManyField(
        MyUser,
        through='Favorite',
        related_name='favorite_recipes'
    )
    in_carts = models.ManyToManyField(
        MyUser,
        through='ShoppingCart',
        related_name='cart_recipes'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name} - Автор: {self.author.username}'


class RecipeIngredient(models.Model):
    """Промежуточная таблица связи рецепта и ингридиента"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(
            1,
            message='Количество должно быть не менее 1'
        )]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}'


class Favorite(models.Model):
    """Модель избранных рецептов"""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Избранные рецепты',
        related_name='favorites',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        MyUser,
        verbose_name='Пользователь',
        related_name='favorites',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} избранные рецепты: {self.recipe}'


class ShoppingCart(models.Model):
    """Модель списка покупок"""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепты в списке покупок',
        related_name='shopping_carts',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        MyUser,
        verbose_name='Список пользователя',
        related_name='carts',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'Список покупок {self.user}: {self.recipe}'

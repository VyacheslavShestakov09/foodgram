import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User

from . import constants


class Tag(models.Model):
    """Тэги для рецептов."""
    name = models.CharField(
        verbose_name='Тэг',
        unique=True,
        max_length=constants.TAG_NAME_MAX_LENGTH,
    )
    slug = models.SlugField(
        verbose_name='Слаг тэга',
        unique=True,
        max_length=constants.TAG_SLUG_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} ({self.slug})'


class Ingredient(models.Model):
    """Ингредиент для рецепта."""
    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=constants.INGREDIENT_NAME_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        max_length=constants.INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_name_unit'
            ),
        )

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Recipe(models.Model):
    """Модель для рецепта."""
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=constants.RECIPE_NAME_MAX_LENGTH,
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True,
    )
    image = models.ImageField(
        verbose_name='Изображение блюда',
        upload_to='recipe_images'
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
        validators=[
            MinValueValidator(
                constants.COOKING_TIME_MIN,
                message=(
                    f'Время приготовления не может быть меньше '
                    f'{constants.COOKING_TIME_MIN}'
                )
            ),
            MaxValueValidator(
                constants.COOKING_TIME_MAX,
                message=(
                    f'Время приготовления не может быть больше '
                    f'{constants.COOKING_TIME_MAX}'
                )
            )
        ]
    )
    short_code = models.CharField(
        max_length=constants.RECIPE_SHORT_CODE_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Код короткой ссылки'
    )

    def save(self, *args, **kwargs):
        """Генерирует уникальный short_code при создании рецепта."""
        if not self.pk and not self.short_code:
            self.short_code = self.generate_short_code()
        super().save(*args, **kwargs)

    def generate_short_code(self):
        """Генерирует уникальный 10-символьный код."""
        while True:
            code = uuid.uuid4().hex[:constants.RECIPE_SHORT_CODE_MAX_LENGTH]
            if not Recipe.objects.filter(short_code=code).exists():
                return code

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.name} — {self.author.username}'


class RecipeIngredient(models.Model):
    """Промежуточная таблица связи рецепта и ингредиента."""
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
        validators=[
            MinValueValidator(
                constants.MIN_INGREDIENT_AMOUNT,
                message=(
                    f'Количество должно быть не менее'
                    f'{constants.MIN_INGREDIENT_AMOUNT}'
                )
            ),
            MaxValueValidator(
                constants.MAX_INGREDIENT_AMOUNT,
                message=(
                    f'Количество не может быть больше'
                    f'{constants.MAX_INGREDIENT_AMOUNT}'
                )
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ('recipe',)

    def __str__(self):
        return f'{self.recipe.name} — {self.ingredient.name} ({self.amount})'


class Favorite(models.Model):
    """Модель избранных рецептов."""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Избранный рецепт',
        related_name='favorites',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='favorites',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user.username} → {self.recipe.name}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт в списке покупок',
        related_name='shopping_carts',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='carts',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user.username} — {self.recipe.name}'

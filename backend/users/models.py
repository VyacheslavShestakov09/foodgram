from django.db import models
from django.contrib.auth.models import AbstractUser


def user_avatar_path(instance, filename):
    return f'avatars/user_{instance.id}/{filename}'


class MyUser(AbstractUser):
    """Кастомная модель пользователя"""
    username = models.CharField(
        verbose_name='Никнейм',
        max_length=150,
        unique=True,
        help_text='Обязательно для заполенния'
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=150,
        unique=True,
        help_text='Обязательно для заполенния'
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=50,
        help_text='Обязательно для заполенния',
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=50,
        help_text='Обязательно для заполенния'
    )
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        verbose_name='Аватар',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['id']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписки пользователей"""
    user = models.ForeignKey(
        MyUser,
        verbose_name='Подписчики',
        related_name="subscriptions",
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        MyUser,
        verbose_name='Автор рецепта',
        related_name='subscribers',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на: {self.author}'

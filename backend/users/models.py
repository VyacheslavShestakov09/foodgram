from django.contrib.auth.models import AbstractUser
from django.db import models

NAME_MAX_LENGTH = 150


def user_avatar_path(instance, filename):
    return f'avatars/user_{instance.id}/{filename}'


class User(AbstractUser):
    """Кастомная модель пользователя"""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
        help_text='Обязательно для заполенния'
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=NAME_MAX_LENGTH,
        help_text='Обязательно для заполенния',
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=NAME_MAX_LENGTH,
        help_text='Обязательно для заполенния'
    )
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        verbose_name='Аватар',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('last_name', 'first_name', 'username')

    def __str__(self):
        return f'Пользователь № {self.id}: {self.username} ({self.email})'


class Subscription(models.Model):
    """Подписки пользователей"""
    user = models.ForeignKey(
        User,
        verbose_name='Подписчики',
        related_name="subscriptions",
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='subscribers',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            ),
        )

    def __str__(self):
        return f'{self.user} подписан на: {self.author}'

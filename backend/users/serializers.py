import re

from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator

from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import (
    TokenCreateSerializer as DjoserTokenCreateSerializer
)

from .models import MyUser, Subscription

from recipes.models import Recipe


class UserCreateSerializer(BaseUserCreateSerializer):
    """Сериализатор для создания пользователя"""
    username = serializers.CharField(
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        help_text='Обязательно для заполнения'
    )

    class Meta(BaseUserCreateSerializer.Meta):
        model = MyUser
        fields = (
            'id',
            'email',
            'username',
            'password',
            'first_name',
            'last_name'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        """Проверяем, что имя пользователя соответствует требованиям"""
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                'Имя пользователя может содержать только буквы,'
                ' цифры и символы: @/./+/-/_'
            )
        return value

    def validate_password(self, value):
        """Проверяем, что пароль соответствует требованиям безопасности"""
        if len(value) < 8:
            raise serializers.ValidationError(
                'Пароль должен содержать минимум 8 символов'
            )
        return value


class TokenCreateSerializer(DjoserTokenCreateSerializer):
    """Сериализатор для создания токена аутентификации"""
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        """Проверяем, что email и пароль введены"""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                username=email, password=password)
            if not user:
                raise serializers.ValidationError("Неверные учетные данные")
        else:
            raise serializers.ValidationError("Введите email и пароль.")

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = MyUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_avatar(self, obj):
        """
        Возвращает URL аватара пользователя.
        Если аватар не установлен, возвращает None.
        """
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на автора.
        Если пользователь не аутентифицирован — возвращает False.
        """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.subscribers.filter(user=user).exists()


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя"""
    avatar = Base64ImageField(required=True)

    class Meta:
        model = MyUser
        fields = ('avatar',)

    def update(self, instance, validated_data):
        if instance.avatar:
            instance.avatar.delete()
        return super().update(instance, validated_data)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки на пользователя"""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    avatar = serializers.ImageField(source='author.avatar', read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        """
        Проверка на подписку
        Раз объект подписки уже существует, возвращает True
        """
        return True

    def get_recipes(self, obj):
        """Получаем рецепты автора
        Если указано параметр recipes_limit, ограничиваем вывод"""
        from recipes.serializers import RecipeShortSerializer
        request = self.context.get('request')
        recipes = Recipe.objects.filter(author=obj.author)
        limit = request.query_params.get('recipes_limit')
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        """
        Возвращает количество рецептов у автора.
        """
        return Recipe.objects.filter(author=obj.author).count()

    def validate(self, data):
        """
        Валидация подписки:
        - нельзя подписаться на себя
        - нельзя подписаться дважды
        """
        request = self.context.get('request')
        user = request.user
        author_id = self.initial_data.get('author')
        if not author_id:
            raise serializers.ValidationError('Не передан author.')
        try:
            author = MyUser.objects.get(id=author_id)
        except MyUser.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден.')
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )
        return data

from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from users.models import User, Subscription


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
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
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.subscribers.filter(user=request.user).exists()
        )


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя"""
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        """Удаляем старый аватар перед обновлением"""
        if instance.avatar:
            instance.avatar.delete()
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки на пользователя"""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
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
        from api.recipes.serializers import RecipeShortSerializer
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeShortSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        """
        Возвращает количество рецептов у автора.
        """
        return obj.recipes.count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки"""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        """
        Валидация подписки:
        - нельзя подписаться на себя
        - нельзя подписаться дважды
        """
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError({
                'detail': 'Вы уже подписаны на этого пользователя.'
            })
        return data

    def to_representation(self, instance):
        """Преобразуем вывод в формат подписки"""
        return SubscriptionSerializer(
            instance.author,
            context=self.context
        ).data

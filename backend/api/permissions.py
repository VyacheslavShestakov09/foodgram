from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешает редактирование только автору объекта.
    Позволяет:
    - Чтение (GET, HEAD, OPTIONS) для всех
    - Изменение (PUT, PATCH, DELETE) только автору
    - Создание (POST) для аутентифицированных пользователей
    """
    def has_object_permission(self, request, view, obj):
        """Проверяет, что пользователь является автором объекта"""
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )

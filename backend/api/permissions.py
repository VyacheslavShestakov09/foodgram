from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """
    Разрешает редактирование только автору объекта.
    Позволяет:
    - Чтение (GET, HEAD, OPTIONS) для всех
    - Изменение (PUT, PATCH, DELETE) только автору
    - Создание (POST) для аутентифицированных пользователей
    """
    def has_permission(self, request, view):
        """Разрешает доступ для аутентифицированных пользователей"""
        if request.method == 'POST':
            return request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        """Проверяет, что пользователь является автором объекта"""
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Разрешает изменение только администраторам.
    Позволяет:
    - Чтение для всех
    - Изменение только администраторам
    """
    def has_permission(self, request, view):
        """Разрешает доступ администраторам или для безопасных методов"""
        return (
            request.method in SAFE_METHODS
            or (request.user and request.user.is_staff)
        )


class IsAuthenticatedAndOwner(BasePermission):
    """
    Разрешает доступ только владельцу объекта.
    Доступ возможен только для аутентифицированного владельца.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

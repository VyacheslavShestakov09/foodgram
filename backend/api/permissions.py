from rest_framework.permissions import BasePermission



class IsAuthorOrReadOnly(BasePermission):
    """Разрешает редактирование только автору объекта.
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
            request.method in ('GET', 'HEAD', 'OPTIONS')
            or obj.author == request.user
        )


class IsAdminOrReadOnly(BasePermission):
    """Разрешает изменение только администраторам.
    Позволяет:
    - Чтение для всех
    - Изменение только администраторам
    """

    def has_permission(self, request, view):
        """Разрешает доступ только администраторам
        или для GET/HEAD/OPTIONS запросов.
        """
        return (
            request.method in ('GET', 'HEAD', 'OPTIONS')
            or (request.user and request.user.is_staff)
        )


class IsAuthenticatedAndOwner(BasePermission):
    """Разрешает доступ только владельцу объекта.
    Позволяет:
    - Доступ только аутентифицированному владельцу
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

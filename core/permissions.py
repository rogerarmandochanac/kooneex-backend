from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """Permite acceso total solo a administradores"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'


class IsMototaxista(permissions.BasePermission):
    """Permite acceso solo a mototaxistas"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'mototaxista'


class IsPasajero(permissions.BasePermission):
    """Permite acceso solo a pasajeros"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'pasajero'

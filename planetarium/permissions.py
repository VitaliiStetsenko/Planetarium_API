
from rest_framework.permissions import BasePermission, SAFE_METHODS

SAFE_METHODS_POST = ("GET", "HEAD", "OPTIONS", "POST", "DELETE")


class AdminAllOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_staff
        ) or (request.method in SAFE_METHODS)


class AdminAllAuthenticatedReadPostDelete(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_staff
        ) or (
                request.user.is_authenticated
                and request.method
                in SAFE_METHODS_POST
        )

from typing import Any, Union

from django.contrib.auth import get_user_model

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


# Constant

User = get_user_model()


# Permissions

class DenyAll(BasePermission):
    """
    Permission that forbids all access to an object or class.
    """

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return False

    def has_permission(self, request: Request, view: APIView) -> bool:
        return False


class IsOwner(BasePermission):
    """
    Object level permission to only allow owner of an object to modify it. The
    object to check for permissions should either be a user instance or an
    object with a "user" property containing the a user instance.
    """

    def has_object_permission(
            self, request: Request,
            view: APIView, obj:
            Union[User, Any]) -> bool:
        return bool(
            request.user and (
                    obj == request.user or
                    (hasattr(obj, 'user') and request.user == obj.user)
            )
        )


class ReadOnly(BasePermission):
    """
    Only permit read-only request.
    """

    def has_permission(self, request: Request, view: APIView):
        return request.method in SAFE_METHODS

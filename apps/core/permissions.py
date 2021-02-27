from typing import Any, Union

from django.contrib.auth import get_user_model

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


# Constant

User = get_user_model()


# Permissions

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
        return obj == request.user or \
               (hasattr(obj, 'user') and request.user == obj.user)

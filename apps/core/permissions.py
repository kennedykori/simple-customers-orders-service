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
    owner of the object should be passed as the last argument of
    *has_object_permission*.
    """

    def has_object_permission(
            self, request: Request, view: APIView, obj: User) -> bool:
        return obj == request.user

from django.contrib.auth import get_user_model

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import Order


# Permissions

class IsOrderOwner(BasePermission):
    """
    Object level permission to only permit customers of an order to modify it.
    Takes the order instance to check for permissions.
    """

    def has_object_permission(
            self, request: Request,
            view: APIView,
            obj: Order) -> bool:
        return bool(request.user and obj.customer.user == request.user)

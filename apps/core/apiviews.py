from django.contrib.auth.models import User
from django.db.models import QuerySet

from dynamic_rest.viewsets import DynamicModelViewSet

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.views import Response

from .permissions import IsOwner

from .serializers import (
    ChangePasswordSerializer,
    ChangeStaffStatusSerializer,
    UserSerializer
)


# Base ViewSets

class BaseViewSet(DynamicModelViewSet):
    """
    This is the base `ViewSet` from which all other viewsets are derived from.
    """
    ...


class AuditBaseViewSet(BaseViewSet):
    """
    This is the base `ViewSet` for all `AuditBase` models in this project.
    """
    ...


# Viewsets

class UserViewSet(DynamicModelViewSet):
    """
    Users API.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsOwner | IsAdminUser],
        serializer_class=ChangePasswordSerializer)
    def change_password(self, request, pk=None):
        """
        Change the password of the currently logged on user.
        """
        user = self.get_object()
        self.check_object_permissions(request, user)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.data.get('user')['new_password'])
            user.save()
            return Response({'status': 'password changed'})
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAdminUser],
        serializer_class=ChangeStaffStatusSerializer)
    def change_staff_status(self, request, pk=None):
        """
        Change the staff status the currently logged on user.
        """
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        if serializer.is_valid():
            # user.is_staff = serializer.data.get('user')['is_staff']
            # user.save()
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_permissions(self):
        # Get the viewset's default permission classes
        permission_classes = self.permission_classes

        # For the create action, allow even non authenticated users to create
        # user accounts
        if self.action == 'create':
            permission_classes = (AllowAny,)

        return [permission() for permission in permission_classes]

    def get_queryset(self, queryset=None):
        """
        Only admin users should be able to edit/view other user accounts.
        """
        queryset: QuerySet = super().get_queryset(queryset)
        user = self.request.user

        if not user.is_staff:
            queryset = queryset.filter(pk=user.pk)

        return queryset

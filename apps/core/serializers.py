from typing import Dict

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from dynamic_rest.serializers import (
    DynamicModelSerializer,
    WithDynamicSerializerMixin
)

from rest_framework import serializers

from .models import AuditBase, BaseModel


# Base Serializers

class BaseSerializer(DynamicModelSerializer):
    """
    This is the root `Serializer` from which all other serializers in the
    project are derived from.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Run any extra configuration and initialization
        self.__configure__()

    def __configure__(self) -> None:
        """
        Subclasses should override this method in case they want to perform
        extra configuration of extra initialization to a serializer instance.
        """
        ...

    class Meta:
        abstract = True
        model = BaseModel


class AuditBaseSerializer(BaseSerializer):
    """
    This is the base `Serializer` for all `AuditBase` models in this project.
    Audit data is only available to admin users.
    """
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only show audit data to admin users
        user = self.get_user_from_context()
        if not(user and user.is_staff):
            for field in ('created_by', 'updated_at', 'updated_by'):
                self.fields.pop(field, None)

    def create(self, validated_data: Dict) -> AuditBase:
        """
        Creates and returns a new model instance with the provided validated
        data. This implementation also adds the user who made the create
        request as the "creator" of the object if such a user is present.

        :param validated_data: The validated data to use when creating the
        instance.

        :return: the created instance.
        """
        user = self.get_user_from_context()
        validated_data['creator'] = user
        return super().create(validated_data)

    def get_user_from_context(self) -> User:
        """
        Finds and returns the user attached to this serializer's context or
        None if the user isn't found.

        :return: the user attached to this serializer's context or None if the
        user isn't found.
        """
        request = self.context.get('request')
        return request.user if request else None

    def update(self, instance: AuditBase, validated_data: Dict) -> AuditBase:
        """
        Updates and returns the given instance with the given validated data.
        This implementation also adds the user who made the update request as
        the "modifier" of the object if such a user is present.

        :param instance: The instance to update.
        :param validated_data: The validated data to use when updating the
        instance.

        :return: the updated instance.
        """
        user = self.get_user_from_context()
        validated_data['modifier'] = user
        return instance.update(**validated_data)

    class Meta:
        abstract = True
        model = AuditBase


# Serializers

class ChangePasswordSerializer(
        WithDynamicSerializerMixin, serializers.Serializer):
    """
    Serializer allows a user to change his/her password.
    """
    new_password = serializers.CharField()

    def validate_new_password(self, value: str):
        """
        Validate that the new password passes all the set validators.
        """
        request = self.context.get('request')
        user = request.user if request else None

        try:
            validate_password(value, user)
        except ValidationError as err:
            raise serializers.ValidationError(err.error_list)
        return value


class ChangeStaffStatusSerializer(
        WithDynamicSerializerMixin, serializers.Serializer):
    """
    Serializer allows the the staff status of
    """
    is_staff = serializers.BooleanField()


class UserSerializer(DynamicModelSerializer):
    """
    Serializer for the **django.contrib.auth.models.User** model.
    """

    class Meta:
        model = User
        name = 'user'
        fields = ('id', 'username', 'email', 'is_staff', 'password')
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ('is_staff',)

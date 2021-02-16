from typing import Dict

from dynamic_rest.serializers import DynamicModelSerializer
from rest_framework.serializers import StringRelatedField

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
    """
    created_by = StringRelatedField(read_only=True)
    updated_by = StringRelatedField(read_only=True)

    def create(self, validated_data: Dict):
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

    def get_user_from_context(self):
        """
        Finds and returns the user attached to this serializer's context or
        None if the user isn't found.

        :return: the user attached to this serializer's context or None if the
        user isn't found.
        """
        request = self.context.get('request')
        return request.user if request else None

    def update(self, instance: AuditBase, validated_data: Dict):
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

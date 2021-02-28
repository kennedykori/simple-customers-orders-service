from typing import Any, Type

import factory

from django.contrib.auth import get_user_model

from ..models import AuditBase, BaseModel


# Constants

User = get_user_model()


# Model factories

class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for **django.contrib.auth.User** model.
    """
    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.LazyAttribute(lambda u: '%s@example.test' % u.username)
    password = factory.PostGenerationMethodCall('set_password', 'changeme')
    is_staff = False

    class Meta:
        model = User
        django_get_or_create = ('username',)


class AdminFactory(UserFactory):
    """
    Factory for **django.contrib.auth.User** model with every created
    instance having the *is_staff* option set to *True*.
    """
    username = factory.Sequence(lambda n: 'admin%d' % n)
    is_staff = True


class BaseFactory(factory.django.DjangoModelFactory):
    """
    Base factory for all non-singleton django models in this project.
    """

    class Meta:
        abstract = True
        model = BaseModel


# noinspection PyProtectedMember
class AuditBaseFactory(BaseFactory):
    """
    Base factory for all **AuditBase** models in this project.
    """
    created_by = factory.SubFactory(UserFactory)

    @classmethod
    def _build(
            cls, model_class: Type[AuditBase],
            *args: Any,
            **kwargs: Any) -> AuditBase:
        if args:
            kwargs.setdefault('created_by', args[0])
        return model_class(**kwargs)

    @classmethod
    def _create(
            cls, model_class: Type[AuditBase],
            *args: Any,
            **kwargs: Any) -> AuditBase:
        return model_class._meta.default_manager.create(*args, **kwargs)

    class Meta:
        abstract = True
        inline_args = ('created_by',)
        model = AuditBase

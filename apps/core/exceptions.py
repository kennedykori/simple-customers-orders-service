from django.core.exceptions import ValidationError


# Exceptions

class ModelValidationError(ValidationError):
    """
    Raise from within a model instance to indicate an invalid state.

    This error is compatible with and accepts the same arguments as
    `django.core.exceptions.ValidationError`. Subclasses of
    `apps.core.models.ValidateMixin` should raise this error to indicate that
    an instance is in an invalid state.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

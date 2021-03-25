from typing import Callable, Collection, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Model
from django.db.models.fields import Field

from ..exceptions import ModelValidationError


# Constants

# Default Model Validation Settings
DEFAULT_MODEL_VALIDATION_SETTINGS = {
    'DISABLE_MODEL_VALIDATION': False,
    'VALIDATE_NON_EDITABLES': False,
    'VALIDATE_ON_SAVE': True
}


# Helpers

def get_model_validation_settings(setting_name: str) -> bool:
    """
    Return the value of given model validation setting.

    If the given model validation setting is not set, then return the default
    value.

    :param setting_name: The name of the setting whose value to return.

    :return: the value of the model validation setting with the given name.

    :raise AttributeError: If the given setting name is not a valid name for
           the available model validation settings.
    """
    if setting_name not in DEFAULT_MODEL_VALIDATION_SETTINGS:
        raise AttributeError("Invalid setting: '%s'" % setting_name)

    setting_val: bool
    try:
        # Check if present in user settings
        setting_val = getattr(settings, 'MODEL_VALIDATION', {})[setting_name]
    except KeyError:
        # Fall back to defaults
        setting_val = DEFAULT_MODEL_VALIDATION_SETTINGS[setting_name]

    return setting_val


# Mixins

class ValidateMixin(Model):
    """
    Model validation helpers.

    Defines model validation characteristics and adds field level validation
    support for models similar to
    `DRF Serializers <https://www.django-rest-framework.org/api-guide/serializers/#field-level-validation/>`_.
    The validation will be run anytime the model's `.full_clean` method is
    called or anytime the model's `.save` method is called.

    To disable model validation when saving for the entire project, set the
    `MODEL_VALIDATION.VALIDATE_ON_SAVE` setting to ``False``. To disable this
    behaviour for a particular instance, set it's `.validate_on_save` property
    to ``False``. Model validation for the entire project can be disabled using
    the `MODEL_VALIDATION.DISABLE_MODEL_VALIDATION` setting. To disable model
    validation for a given instance, set it's `.disable_model_validation`
    property to ``True``. With model validation disabled, validation will be
    skipped regardless of whether the `.full_clean` or `.save` method is
    called. This however should be used with caution as it can lead to broken
    invariants and invalid instances.

    Like `DRF Serializers`, custom validation for fields can be specified by
    adding `.validate_<field_name>` methods to models that inherit from this
    mixin. However, unlike DRF Serializers' field level validation, the
    following conditions hold for this mixin's field validation methods:

    #. The field validation methods don't accept any arguments(expect
       ``self``). To access the field value, use `self.<field_name>`.
    #. The validate methods are not required to return anything. Any returned
       value will be ignored.
    #. In case of an invalid value, an
       `apps.core.exceptions.ModelValidationError` should be raised. If there
       are no errors to report, the validate methods should return cleanly.
    #. Validation will be run for all fields with a validate method. This
       includes non-editable fields(i.e. fields whose `editable` parameter is
       set to ``True``), if the model's `.validate_non_editables` parameter is
       set to ``True``.

    Here's an example::

        class Person(Model, ValidationMixin):
            name = models.CharField(max_length=50)
            age = models.PositiveIntegerField()

            def validate_name(self) -> None:
                \"""
                Check that the name has at least 3 characters.
                \"""
                from django.core.exceptions import ValidationError

                if len(self.name) < 3:
                    raise ModelValidationError(
                        message='A valid name should have at least 3 chars',
                        code='invalid'
                    )

            def validate_age(self) -> None:
                \"""
                Check that the person is a youth.
                \"""
                from django.core.exceptions import ValidationError

                if age < 18 or age > 35:
                    raise ModelValidationError(
                        message='Only youths are allowed',
                        code='invalid'
                    )

    Multi-field validation can easily be achieved by simply accessing other
    fields' values from another field's validation method using direct field
    access, i.e. `self.<other_field>`. Nonetheless, the method `.validate`
    should be used for multi-level/object-level validation. Subclasses should
    override this method and add their validation logic. This method should not
    return any value and should raise
    `apps.core.exceptions.ModelValidationError` if validation errors are
    present.
    """

    # Validation can be tuned/configured using the following project settings/
    # model settings overrides.
    disable_model_validation: bool = get_model_validation_settings(
        'DISABLE_MODEL_VALIDATION'
    )
    """The default disable validation setting for this model's instances."""

    validate_non_editables: bool = get_model_validation_settings(
        'VALIDATE_NON_EDITABLES'
    )
    """
    The default validate non-editable fields setting for this model's 
    instances.
    """

    validate_on_save: bool = get_model_validation_settings('VALIDATE_ON_SAVE')
    """The default validate on save setting for this model's instances."""

    def clean_fields(self, exclude: Optional[Collection[str]] = None) -> None:
        """
        Extend the default `.clean_fields()` implementation to handle custom
        field level validation.

        :param exclude: A list of field names to be skipped during validation.

        :raise ModelValidationError: if validation errors are present.
        """
        if self.disable_model_validation:
            # Skip validation
            return

        exclude = exclude or tuple()
        clean_fields_errors: Optional[ValidationError] = None
        validate_fields_errors: Optional[ModelValidationError] = None

        # Run `.clean_fields` and `.validate_fields` and catch any errors that
        # might be present. Later, those errors will be appended to the final
        # `ModelValidationError` that will be raised from this method.
        try:
            super().clean_fields(exclude)
        except ValidationError as ce:
            clean_fields_errors = ce

        # Field-level validation
        try:
            self.validate_fields(exclude)
        except ModelValidationError as ve:
            validate_fields_errors = ve

        # If there were no validation errors, exit cleanly
        if not(clean_fields_errors or validate_fields_errors):
            return

        # Create a new error and fill it with the correct error details
        error = ModelValidationError({})
        if clean_fields_errors:
            error.update_error_dict(clean_fields_errors.error_dict)
        if validate_fields_errors:
            error.update_error_dict(validate_fields_errors.error_dict)

        # Raise the validation error
        raise error

    def full_clean(
            self,
            exclude: Optional[Collection[str]] = None,
            validate_unique: bool = True) -> None:
        """
        Extend the default `.full_clean()` implementation to add support for
        custom multi-field/object validation.

        :param exclude: A list of field names to be skipped during validation.
        :param validate_unique: A flag to determine whether `.validate_unique`
               should be performed or not.

        :raise ModelValidationError: If validation errors are present.
        """
        if self.disable_model_validation:
            # Skip validation
            return

        full_clean_errors: Optional[ValidationError] = None
        validate_errors: Optional[ModelValidationError] = None

        try:
            super().full_clean(exclude, validate_unique)
        except ValidationError as fe:
            full_clean_errors = fe

        try:
            self.validate(exclude)
        except ModelValidationError as ve:
            validate_errors = ve

        # If there were no validation errors, exit cleanly
        if not (full_clean_errors or validate_errors):
            return

        # Create a new error and fill it with the correct error details
        error = ModelValidationError({})
        if full_clean_errors:
            error.update_error_dict(full_clean_errors.error_dict)
        if validate_errors:
            error.update_error_dict(validate_errors.error_dict)

        # Raise the validation error
        raise error

    def run_validation(
            self,
            exclude: Optional[Collection[str]] = None,
            validate_unique: bool = True) -> None:
        """
        Perform a model's validation during save.

        Called when saving a model's instances. Runs all the validation of a
        model including both field level and object level validation.
        Validation will *ONLY* be run if `self.validate_on_save` and
        `self.disable_model_validation` are ``True``. If validation is run and
        validation errors are present, then a `ModelValidationError` will be
        raised.

        :raise ModelValidationError: If validation is run and validation errors
               are present.
        """
        if self.validate_on_save and not self.disable_model_validation:
            # Only proceed with the validation if validation on save is
            # enabled for this instance and validation for this instance is not
            # disabled.
            self.full_clean(exclude, validate_unique)

    def save(self, *args, **kwargs) -> None:
        # Run this model's validation before saving
        self.run_validation()

        super().save(*args, **kwargs)

    def validate(self, exclude: Optional[Collection[str]] = None) -> None:
        """
        Perform multi-field validation for this model.

        Called during the validation phase after field-level validation has
        occurred. Subclasses should override this method and add multi-field
        validation logic. An optional list of the names of the fields that
        should be ignored is given as the only argument. It's up to subclasses
        to decide what to do with this list, either skip validation of the
        fields listed or ignore the list and proceed with the validation of
        those fields anyway. In case validation errors are present,
        `apps.core.exceptions.ModelValidationError` should be raised.

        :param exclude: An optional list of field names to exclude from the
               validation. It's up to subclasses to choose on whether to skip
               validation of the fields listed or to ignore the list.

        :raise ModelValidationError: if validation errors are present.
        """
        ...

    def validate_fields(
            self, exclude: Optional[Collection[str]] = None) -> None:
        """
        Perform field-level validation for the fields in this model.

        Call each `.validate_<field_name>` method of all applicable fields and
        raise a `ModelValidationError` containing a dict of all validation
        errors if any are present. A field is applicable for validation if:

        * It is not in the `exclude` list passed to this method.
        * It is not a non-editable field.
        * If it is a non-editable field, `.validate_non_editables` should be
          set to ``True``.

        :param exclude: A list of field names to be skipped during validation.

        :raise ModelValidationError: if validation errors are present.
        """
        errors = {}

        # Get the fields that will be validated
        field: Field
        fields = [
            field for field in self._meta.get_fields()
            # Skip excluded fields
            if not (field.name in exclude) and (
                # Validate non-editable fields if validation of non editables
                # is enabled.
                field.editable or self.validate_non_editables
            )
        ]

        # Run the field-level validation for each field to be validated
        for field in fields:
            validate_method: Optional[Callable[[], None]] = getattr(
                self,
                'validate_' + field.name,
                None
            )
            if validate_method:
                try:
                    validate_method()
                except ValidationError as err:
                    errors[field.name] = err

        if errors:
            raise ModelValidationError(errors)

    class Meta:
        abstract = True

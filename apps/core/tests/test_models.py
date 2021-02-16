from django.test import TestCase


# Base TestCase

class BaseModelTestCase(TestCase):
    """
    This is the base `TestCase` for all the models in the project.
    """
    ...


class AuditBaseTestCase(BaseModelTestCase):
    """
    This is the base `TestCase` for all the `AuditBase` models in the
    project.
    """
    ...


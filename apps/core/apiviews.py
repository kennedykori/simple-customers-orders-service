from dynamic_rest.viewsets import DynamicModelViewSet


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

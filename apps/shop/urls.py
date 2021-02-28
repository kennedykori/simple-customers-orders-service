from django.urls import include, path

from dynamic_rest.routers import DynamicRouter

from .apiviews import (
    CustomerViewSet,
    EmployeeViewSet,
    InventoryViewSet,
    OrderViewSet,
    OrderItemViewSet
)


router = DynamicRouter()
router.register('customers', CustomerViewSet)
router.register('employees', EmployeeViewSet)
router.register('inventories', InventoryViewSet)
router.register('orders', OrderViewSet)
router.register('order-items', OrderItemViewSet)

urlpatterns = [
    path('', include(router.urls))
]

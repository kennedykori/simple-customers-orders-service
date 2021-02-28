from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import Response

from ..core.apiviews import AuditBaseViewSet
from ..core.permissions import DenyAll, IsOwner,ReadOnly

from .exceptions import (
    NotEnoughStockError,
    OrderEmptyError,
    OperationForbiddenError
)
from .models import Customer, Employee, Inventory, Order, OrderItem
from .permissions import IsOrderOwner
from .serializers import (
    CustomerSerializer,
    EditOrderStateSerializer,
    EditOrderItemListSerializer,
    EmployeeSerializer,
    InventorySerializer,
    LimitedInventorySerializer,
    NewOrderSerializer,
    OrderSerializer,
    OrderItemSerializer
)


# Viewsets

class CustomerViewSet(AuditBaseViewSet):
    """
    Customers API.
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self, queryset=None):
        queryset = super().get_queryset(queryset)
        user = self.request.user

        if not user.is_staff:
            queryset = queryset.filter(user=user)

        return queryset

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsOwner | IsAdminUser],
        serializer_class=NewOrderSerializer)
    def make_order(self, request, pk=None):
        """
        Make a new order for this customer.
        """
        customer = self.get_object()
        self.check_object_permissions(request, customer.user)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployeeViewSet(AuditBaseViewSet):
    """
    Employees API.
    """
    queryset = Employee.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = EmployeeSerializer


class InventoryViewSet(AuditBaseViewSet):
    """
    Inventory API.
    """
    queryset = Inventory.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = InventorySerializer

    def get_permissions(self):
        permission_classes = self.permission_classes

        if self.action == 'list' or self.action == 'metadata' or \
                self.action == 'retrieve':
            permission_classes = (AllowAny,)

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        user = self.request.user
        if not (user and user.is_staff):
            return LimitedInventorySerializer
        return self.serializer_class


class OrderViewSet(AuditBaseViewSet):
    """
    Orders API.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        permission_classes = self.permission_classes

        # Disable direct updates to orders. All updates to order instances
        # should be performed through extra actions
        if self.action in ('partial_update', 'update'):
            permission_classes = (DenyAll,)

        return [permission() for permission in permission_classes]

    def get_queryset(self, queryset=None):
        queryset = super().get_queryset(queryset)
        user = self.request.user

        if not user.is_staff:
            queryset = queryset.filter(customer__user=user)

        return queryset

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)

        if self.action == 'approve':
            serializer = self.serializer_class(
                action=EditOrderStateSerializer.Action.approve,
                context=self.get_serializer_context(),
                *args,
                **kwargs
            )
        elif self.action == 'cancel':
            serializer = self.serializer_class(
                action=EditOrderStateSerializer.Action.cancel,
                context=self.get_serializer_context(),
                *args,
                **kwargs
            )
        elif self.action == 'reject':
            serializer = self.serializer_class(
                action=EditOrderStateSerializer.Action.reject,
                context=self.get_serializer_context(),
                *args,
                **kwargs
            )
        elif self.action == 'remove_item':
            serializer = self.serializer_class(
                action=EditOrderItemListSerializer.Action.remove_item,
                context=self.get_serializer_context(),
                *args,
                **kwargs
            )
        elif self.action == 'update_item':
            serializer = self.serializer_class(
                action=EditOrderItemListSerializer.Action.update_item,
                context=self.get_serializer_context(),
                *args,
                **kwargs
            )

        return serializer

    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()

        if self.action == 'create':
            serializer_class = NewOrderSerializer

        return serializer_class

    ##########################################################################
    # ORDER ITEM LIST MUTATORS
    ##########################################################################
    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(IsAdminUser | IsOrderOwner,),
        serializer_class=EditOrderItemListSerializer)
    def add_item(self, request, pk=None):
        """
        Add a new inventory item to this order.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order_item = serializer.save()
        except OperationForbiddenError as e:
            return Response(
                {'detail': e.args[0]},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        return Response(
            OrderItemSerializer(order_item).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(IsAdminUser | IsOrderOwner,),
        serializer_class=EditOrderItemListSerializer)
    def remove_item(self, request, pk=None):
        """
        Remove an inventory item from this order.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            serializer.save()
        except OperationForbiddenError as e:
            return Response(
                {'detail': e.args[0]},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(IsAdminUser | IsOrderOwner,),
        serializer_class=EditOrderItemListSerializer)
    def update_item(self, request, pk=None):
        """
        Update an inventory item in this order.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order_item = serializer.save()
        except OperationForbiddenError as e:
            return Response(
                {'detail': e.args[0]},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        return Response(
            OrderItemSerializer(order_item).data,
            status=status.HTTP_200_OK
        )

    ##########################################################################
    # ORDER STATE MUTATORS
    ##########################################################################
    @action(
        detail=True,
        methods=['PATCH'],
        permission_classes=(IsAdminUser,),
        serializer_class=EditOrderStateSerializer)
    def approve(self, request, pk=None):
        """
        Approve this order. Only employees can approve orders.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = serializer.save()
        except NotEnoughStockError as e:
            return Response(
                {
                    'adjustment': e.adjustment_amount,
                    'available_stock': e.item.on_hand,
                    'detail': e.message,
                    'item': e.item.pk
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except OperationForbiddenError as e:
            return Response(
                {'detail': e.args[0]},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        except OrderEmptyError as e:
            return Response(
                {'detail': e.message},
                status=status.HTTP_424_FAILED_DEPENDENCY
            )

        return Response(
            OrderSerializer(
                order,
                context=self.get_serializer_context()
            ).data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['PATCH'],
        permission_classes=(IsAdminUser | IsOrderOwner,),
        serializer_class=EditOrderStateSerializer)
    def cancel(self, request, pk=None):
        """
        Cancel this order.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = serializer.save()
        except OperationForbiddenError as e:
            return Response(
                {'detail': e.args[0]},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        return Response(
            OrderSerializer(
                order,
                context=self.get_serializer_context()
            ).data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['PATCH'],
        permission_classes=(IsAdminUser | IsOrderOwner,),
        serializer_class=EditOrderStateSerializer)
    def mark_ready_for_review(self, request, pk=None):
        """
        Mark this order as ready for review.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = serializer.save()
        except OperationForbiddenError as e:
            return Response(
                {'detail': e.args[0]},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        except OrderEmptyError as e:
            return Response(
                {'detail': e.message},
                status=status.HTTP_424_FAILED_DEPENDENCY
            )

        return Response(
            OrderSerializer(
                order,
                context=self.get_serializer_context()
            ).data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['PATCH'],
        permission_classes=(IsAdminUser,),
        serializer_class=EditOrderStateSerializer)
    def reject(self, request, pk=None):
        """
        Reject this order. Only employees can reject orders.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = serializer.save()
        except OperationForbiddenError as e:
            return Response(
                {'detail': e.args[0]},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        return Response(
            OrderSerializer(
                order,
                context=self.get_serializer_context()
            ).data,
            status=status.HTTP_200_OK
        )


class OrderItemViewSet(AuditBaseViewSet):
    """
    Order Items API.
    """
    queryset = OrderItem.objects.all()
    permission_classes = (IsAdminUser | (IsAuthenticated & ReadOnly),)
    serializer_class = OrderItemSerializer

    def get_queryset(self, queryset=None):
        queryset = super().get_queryset(queryset)
        user = self.request.user

        # Non admin users should only be able to see order items that they own
        if not(user and user.is_staff):
            queryset = queryset.filter(order__customer__user=user)

        return queryset

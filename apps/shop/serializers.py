from enum import Enum
from typing import Optional

from django.contrib.auth import get_user_model

from dynamic_rest.serializers import DynamicRelationField

from rest_framework import serializers

from ..core.serializers import AuditBaseSerializer

from .models import (
    ZERO_AMOUNT,
    Customer,
    Employee,
    Inventory,
    Order,
    OrderItem
)

# Constants

User = get_user_model()


# Serializers

class EditOrderItemListSerializer(AuditBaseSerializer):
    """
    Serializer for making modifications to an **Order's** item list.
    """
    item = serializers.PrimaryKeyRelatedField(
        queryset=Inventory.objects.all()
    )
    quantity = serializers.IntegerField(min_value=1, required=False)
    unit_price = serializers.DecimalField(
        decimal_places=2,
        max_digits=5,
        min_value=ZERO_AMOUNT,
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.action: EditOrderItemListSerializer.Action = kwargs.pop(
            'action',
            self.Action.add_item
        )
        super().__init__(*args, **kwargs)
        # When the current action is remove, hide unneeded fields
        if self.action == EditOrderItemListSerializer.Action.remove_item:
            self.fields.pop('quantity', None)
            self.fields.pop('unit_price', None)

    def __configure__(self):
        super().__configure__()
        item_field = self.fields.get('item', None)
        user = self.get_user_from_context()

        # Disallow adding items that are out of stock
        if self.action == EditOrderItemListSerializer.Action.add_item:
            if item_field:
                item_field.queryset = Inventory.objects.exclude(on_hand=0)

    def update(self, instance: Order, validated_data) -> OrderItem:
        user = self.get_user_from_context()

        # Only staff members should be allowed to change the price of an item
        if not (user and user.is_staff):
            validated_data.pop('unit_price', None)

        if self.action == EditOrderItemListSerializer.Action.add_item:
            return instance.add_item(user, **validated_data)
        elif self.action == EditOrderItemListSerializer.Action.remove_item:
            validated_data.pop('quantity', None)
            return instance.remove_item(**validated_data)

        return instance.update_item(user, **validated_data)

    # noinspection PyMethodMayBeStatic
    def validate(self, data):
        item: Inventory = data['item']
        order: Order = self.instance

        if self.action == EditOrderItemListSerializer.Action.add_item:
            if item in map(lambda oi: oi.item, order.orderitem_set.all()):
                raise serializers.ValidationError({
                    'item': 'This item already exists in this order.'
                })
        elif self.action == EditOrderItemListSerializer.Action.remove_item or\
                self.action == EditOrderItemListSerializer.Action.update_item:
            if not self.instance.has_item(item):
                raise serializers.ValidationError({
                    'item': "This item doesn't exists in this order."
                })

        return data

    class Action(Enum):
        add_item = 'ADD'
        remove_item = 'REMOVE'
        update_item = 'UPDATE'

    class Meta:
        model = Order
        name = 'order_item'
        fields = ('item', 'quantity', 'unit_price')


class EditOrderStateSerializer(AuditBaseSerializer):
    """
    Serializer for making modifications to an **Order's** state.
    """
    comments = serializers.CharField(
        allow_null=True,
        max_length=1000,
        required=False,
        style={'base_template': 'textarea.html'}
    )

    def __init__(self, *args, **kwargs):
        self.action: EditOrderStateSerializer.Action = kwargs.pop(
            'action',
            self.Action.mark_ready
        )
        super().__init__(*args, **kwargs)
        # When the current action is mark_ready, hide unneeded fields
        if self.action == EditOrderStateSerializer.Action.approve:
            handler_field = self.fields.get('handler')
            if handler_field:
                handler_field.allow_null = False
                handler_field.required = True
        elif self.action == EditOrderStateSerializer.Action.cancel:
            self.fields.pop('handler', None)
        elif self.action == EditOrderStateSerializer.Action.mark_ready:
            self.fields.pop('comments', None)
            self.fields.pop('handler', None)
        elif self.action == EditOrderStateSerializer.Action.reject:
            comments_field = self.fields.get('comments')
            handler_field = self.fields.get('handler')
            if comments_field:
                comments_field.allow_null = False
                comments_field.min_length = 3
                comments_field.required = True
            if handler_field:
                handler_field.allow_null = False
                handler_field.required = True

    def update(self, instance: Order, validated_data) -> Order:
        user: User = self.get_user_from_context()

        if self.action == EditOrderStateSerializer.Action.approve:
            handler: Employee = validated_data.pop('handler')
            validated_data['employee'] = handler
            instance.approve(**validated_data)
        elif self.action == EditOrderStateSerializer.Action.cancel:
            instance.cancel(user, **validated_data)
        elif self.action == EditOrderStateSerializer.Action.mark_ready:
            instance.mark_ready_for_review(user)
        elif self.action == EditOrderStateSerializer.Action.reject:
            handler: Employee = validated_data.pop('handler')
            validated_data['employee'] = handler
            instance.reject(**validated_data)

        return instance

    class Action(Enum):
        approve = 'APPROVE'
        cancel = 'CANCEL'
        mark_ready = 'MARK_READY'
        reject = 'REJECT'

    class Meta:
        model = Order
        name = 'order'
        fields = ('comments', 'handler')


class EmployeeSerializer(AuditBaseSerializer):
    """
    Serializer for the **Employee** model.
    """

    def __configure__(self) -> None:
        super().__configure__()
        # An employee can only be an admin and if an employee already exists,
        # they shouldn't be able to change their associated user object
        user_field = self.fields.get('user', None)
        if self.instance and isinstance(self.instance, Employee) and \
                user_field:
            user_field.queryset = User.objects.filter(
                pk=self.instance.user.pk
            )
        elif user_field:
            user_field.queryset = User.objects.filter(is_staff=True)

    class Meta:
        model = Employee
        name = 'employee'
        fields = '__all__'


class InventorySerializer(AuditBaseSerializer):
    """
    Serializer for the **Inventory** model.
    """
    state = serializers.CharField(read_only=True)

    class Meta:
        model = Inventory
        name = 'inventory'
        fields = '__all__'


class LimitedInventorySerializer(InventorySerializer):
    """
    Serializer for the **Inventory** model. This serializer limits the
    information it outputs and is read only. It should be used for showing
    inventory info to non-staff users.
    """

    class Meta:
        model = Inventory
        name = 'inventory'
        fields = (
            'id', 'beverage_name', 'beverage_type', 'caffeinated',
            'flavored', 'price', 'state'
        )
        read_only_fields = fields


class OrderItemSerializer(AuditBaseSerializer):
    """
    Serializer for the **OrderItem** model.
    """
    order = DynamicRelationField('OrderSerializer')
    item = DynamicRelationField(InventorySerializer)
    total_price = serializers.DecimalField(
        decimal_places=2,
        max_digits=7,
        min_value=ZERO_AMOUNT,
        read_only=True
    )

    def __configure__(self) -> None:
        super().__configure__()
        order_field = self.fields.get('order', None)
        user = self.get_user_from_context()
        # None staff users shouldn't be able to view other user's orders
        if order_field and user and not user.is_staff:
            order_field.queryset = Order.objects.filter(customer__user=user)

    def create(self, validated_data) -> OrderItem:
        order: Order = validated_data.pop('order')
        user = self.get_user_from_context()

        # Only staff members should be allowed to change the price of an item
        if not(user and user.is_staff):
            validated_data.pop('unit_price', None)
        return order.add_item(user, **validated_data)

    class Meta:
        model = OrderItem
        name = 'order_item'
        fields = '__all__'


class OrderSerializer(AuditBaseSerializer):
    """
    Serializer for the **Order** model.
    """
    customer = DynamicRelationField('CustomerSerializer')
    handler = DynamicRelationField(EmployeeSerializer)
    order_items = OrderItemSerializer(
        embed=True,
        many=True,
        read_only=True,
        source='orderitem_set'
    )
    total_price = serializers.DecimalField(
        decimal_places=2,
        max_digits=7,
        min_value=ZERO_AMOUNT,
        read_only=True
    )

    class Meta:
        model = Order
        name = 'order'
        fields = '__all__'
        deferred_fields = ('order_items',)


class NewOrderSerializer(OrderSerializer):
    """
    This is the serializer used when creating a new **Order**.
    """
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all()
    )

    def __configure__(self):
        super().__configure__()
        # Enforce that all non-staff user's cannot see other details of other
        # customers not associated with them.
        customer_field = self.fields.get('customer', None)
        user = self.get_user_from_context()
        if customer_field and user and not user.is_staff:
            customer_field.queryset = Customer.objects.filter(user=user)

    class Meta:
        model = Order
        name = 'order'
        fields = (
            'id', 'created_at', 'customer', 'state', 'order_items',
            'total_price'
        )
        read_only_fields = ('handler', 'state')


class CustomerSerializer(AuditBaseSerializer):
    """
    Serializer for the **Customer** model.
    """
    orders = OrderSerializer(
        embed=True,
        many=True,
        read_only=True,
        source='order_set'
    )

    def __configure__(self) -> None:
        super().__configure__()
        # A customer cannot be an admin and if a customer already exists, they
        # shouldn't be able to change their associated user object
        user_field = self.fields.get('user', None)
        if self.instance and isinstance(self.instance, Customer) and \
                user_field:
            user_field.queryset = User.objects.filter(
                pk=self.instance.user.pk
            )
        elif user_field:
            user_field.queryset = User.objects.filter(is_staff=False)

    class Meta:
        model = Customer
        name = 'customer'
        fields = '__all__'
        deferred_fields = ('orders',)

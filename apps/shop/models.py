from __future__ import annotations
from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models, transaction
from django.utils.timezone import now

from ..core.enums import Choices
from ..core.exceptions import ModelValidationError
from ..core.models import AuditBase, AuditBaseManager


# Constants

User = get_user_model()

ZERO_AMOUNT = Decimal('0.00')


# Managers

class OrderItemManager(AuditBaseManager):
    """
    Manager for the ``OrderItem`` model.
    """

    def create(self, creator: User = None, *args, **kwargs) -> OrderItem:
        """
        Creates a new ``OrderItem`` with the given properties and by the given
        creator. This override extends the default implementation of this
        method to prohibit non-staff users from being able to specify the unit
        price of an item. If the creator argument is not provided or contains
        a non-staff user, then the ``unit_price`` of the created instance will
        be set to the current price of the provided inventory item.

        Also, if the ``unit_price`` is not provided, then it will default to
        the current price of the provided inventory item regardless of the user
        creating the order item.

        :param creator: The user who initiated this create/request.
        :param args: Positional arguments to use when creating the order item.
        :param kwargs: Key-word arguments to use when creating the order item.

        :return: the created order item.
        """
        item: Optional[Inventory] = kwargs.get('item', None)
        unit_price: Optional[Decimal] = kwargs.get('unit_price', None)
        if (unit_price is None or creator is None or not creator.is_staff)\
                and item is not None:
            kwargs['unit_price'] = item.price

        order_item: OrderItem = super().create(creator, *args, **kwargs)
        return order_item


# Models

class Customer(AuditBase):
    """
    This model represents a customer of the beverage shop. Customers can make
    beverage orders from the beverage shop.
    """
    name = models.CharField(max_length=250)
    address = models.CharField(max_length=250, blank=True, null=True)
    phone_number = models.CharField(max_length=13)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    def make_order(self) -> Order:
        """
        Creates and returns a new **Order** for this **Customer**.

        :return: the newly created Order instance.
        """
        return Order.objects.create(self.user, customer=self)

    def validate_created_by(self):
        """
        Ensure that only admin/staff users or the user instance associated with
        the customer can add the customer.
        """
        creator: Optional[User] = getattr(self, 'created_by', None)
        user: Optional[User] = getattr(self, 'user', None)

        # If a "creator" has been provided, then the value must be a staff user
        # or the user instance associated with this customer.
        if creator and user and not creator.is_staff and creator != user:
            raise ModelValidationError(
                'Only staff users or the user to be associated with the '
                'customer can add the customer.',
                code='invalid'
            )

    def validate_updated_by(self):
        """
        Ensure that only admin/staff users or the user instance associated with
        the customer can modify the customer's details.
        """
        modifier: Optional[User] = getattr(self, 'updated_by', None)
        user: Optional[User] = getattr(self, 'user', None)

        # If a "modifier" has been provided, then the value must be a staff
        # user or the user instance associated with this customer.
        if modifier and user and not modifier.is_staff and modifier != user:
            raise ModelValidationError(
                'Only staff users or the user associated with the customer '
                "can modify the customer's details.",
                code='invalid'
            )

    def validate_user(self):
        """
        Ensure that the user instance associated with a customer is a non-staff
        user.
        """
        user: Optional[User] = getattr(self, 'user', None)

        # Ensure that a value for the user property has been provided
        if user is None:
            raise ModelValidationError(
                'Please provide the user instance associated with this '
                'customer.',
                code='required'
            )
        # Ensure that the user instance provided is not a non-staff user
        if user.is_staff:
            raise ModelValidationError(
                'The user instance provided must be a non-staff user.',
                code='invalid'
            )

    def __str__(self):
        return self.name


class Employee(AuditBase):
    """
    This model represents an employee of the beverage shop. The main role of
    an employee is to review/handle customer orders but employees can also
    make orders on behalf of the customers.
    """

    class Gender(Choices):
        """
        This represents the gender of a person.
        """
        MALE = ('M', 'MALE')
        FEMALE = ('F', 'FEMALE')

    name = models.CharField(max_length=250)
    gender = models.CharField(
        max_length=1,
        choices=Gender.to_list(),
        default=Gender.MALE.choice_value
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    def validate_created_by(self):
        """
        Ensure that only admin/staff users can add new employees.
        """
        creator: Optional[User] = getattr(self, 'created_by', None)

        # If a "creator" has been provided, then the value must be a staff user
        if creator and not creator.is_staff:
            raise ModelValidationError(
                'Only staff users can add new employees.',
                code='invalid'
            )

    def validate_updated_by(self):
        """
        Ensure that only admin/staff users can modify existing employees data.
        """
        modifier: Optional[User] = getattr(self, 'updated_by', None)

        # If a "modifier" has been provided, then the value must be a staff
        # user
        if modifier and not modifier.is_staff:
            raise ModelValidationError(
                'Only staff users can modify existing employees data.',
                code='invalid'
            )

    def validate_user(self):
        """
        Ensure that the user instance associated with an employee is always a
        staff user.
        """
        user: User = getattr(self, 'user', None)

        # Ensure that a value for the user property has been provided
        if user is None:
            raise ModelValidationError(
                'Please provide the user instance associated with this '
                'employee.',
                code='required'
            )
        # Ensure that the user instance provided is a staff user
        if not user.is_staff:
            raise ModelValidationError(
                'The user instance provided must be a staff user.',
                code='invalid'
            )

    def __str__(self):
        return self.name


class Inventory(AuditBase):
    """
    This model represents all the items(beverages) offered by the beverage
    shop.
    """

    class BeverageTypes(Choices):
        """The different types of beverages in the shop."""
        COFFEE = ('C', 'COFFEE')
        TEA = ('T', 'TEA')

    class InventoryItemState(Choices):
        """
        The different availability states of an item in the **Inventory**.
        """
        AVAILABLE = ('A', 'AVAILABLE')
        FEW_REMAINING = ('F', 'FEW REMAINING')
        OUT_OF_STOCK = ('O', 'OUT OF STOCK')

    beverage_name = models.CharField(max_length=150)
    beverage_type = models.CharField(
        max_length=1,
        choices=BeverageTypes.to_list(),
        default=BeverageTypes.COFFEE.choice_value
    )
    caffeinated = models.BooleanField(default=False)
    flavored = models.BooleanField(default=False)
    on_hand = models.PositiveIntegerField(default=0)
    price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=ZERO_AMOUNT
    )
    warn_limit = models.PositiveIntegerField(default=3)

    @property
    def is_available(self) -> bool:
        """
        Returns *True* to indicate that there is enough stock for this item,
        *False* otherwise.

        :return: True to indicate that there is enough stock for this item,
                 False otherwise.
        """
        return self.on_hand > self.warn_limit

    @property
    def is_few_remaining(self) -> bool:
        """
        Returns *True* to indicate the number of this items remaining in stock
        are equal or fewer than this item's warn limit or *False* otherwise.

        :return: True to indicate that items equal or fewer that this item's
                 warn limit remain in stock, False otherwise.
        """
        return self.on_hand <= self.warn_limit

    @property
    def is_out_of_stock(self) -> bool:
        """
        Returns *True* to indicate that this item's stock has been depleted,
        *False* otherwise.

        :return: True if this item's stock has been depleted, False otherwise.
        """
        return self.on_hand == 0

    @property
    def state(self) -> str:
        """
        Returns the current availability state of this item. The possible
        states are:

        * **AVAILABLE** - Indicates that there are plenty of items in the
          stock, that is, items greater than this item's warn limit.
        * **FEW REMAINING** - Indicates that items equal or fewer than this
          item's warn limit are remaining in stock.
        * **OUT OF STOCK** - Indicates that there are no items remaining in
          stock.

        :return: the current availability state of this item.
        """
        if self.is_out_of_stock:
            return Inventory.InventoryItemState.OUT_OF_STOCK.choice_display
        elif self.is_few_remaining:
            return Inventory.InventoryItemState.FEW_REMAINING.choice_display
        # For the default case, return AVAILABLE
        return Inventory.InventoryItemState.AVAILABLE.choice_display

    def deduct(self, user: User, quantity: int) -> int:
        """
        Adjusts the on hand quantity of this item by subtracting the current
        on hand quantity of this item by the given quantity. If the resulting
        stock after the deduction is negative, then a **NotEnoughStockError**
        will be raised. A **ValueError** will also be raised if the given
        quantity is a negative value. Returns the remaining stock after the
        deduction.

        :param user: The user performing this operation.
        :param quantity: The quantity to deduct the current stock by. Must be
               a positive value.

        :return: the remaining stock after the deduction.

        :raise NotEnoughStockError: If the deduction would result in negative
               stock.
        :raise ValueError: If quantity is negative.
        """
        from .exceptions import NotEnoughStockError

        # Assert that quantity isn't negative
        if quantity < 0:
            raise ValueError('"quantity" must be a positive value')

        # Perform the deduction and assert that the remaining stock is valid
        new_stock: int = self.on_hand - quantity
        if new_stock < 0:
            raise NotEnoughStockError(self, quantity)

        # Adjust the stock
        self.update(user, on_hand=new_stock)

        # Return the new stock value
        return new_stock

    def validate_created_by(self):
        """
        Ensure that only admin/staff users can add new inventory items.
        """
        creator: Optional[User] = getattr(self, 'created_by', None)

        # If a "creator" has been provided, then the value must be a staff user
        if creator and not creator.is_staff:
            raise ModelValidationError(
                'Only staff users can add new inventory items.',
                code='invalid'
            )

    def validate_on_hand(self):
        """Ensure that the on hand quantity of an item cannot be negative."""
        if self.on_hand < 0:
            raise ModelValidationError(
                'The available quantity of an item cannot be a negative '
                'value.',
                code='invalid'
            )

    def validate_price(self):
        """Ensure that the price of an item cannot be negative."""
        if self.price < ZERO_AMOUNT:
            raise ModelValidationError(
                'The price of an item cannot be negative.',
                code='invalid'
            )

    def validate_updated_by(self):
        """
        Ensure that only admin/staff users can modify existing inventory items.
        """
        modifier: Optional[User] = getattr(self, 'updated_by', None)

        # If a "modifier" has been provided, then the value must be a staff
        # user
        if modifier and not modifier.is_staff:
            raise ModelValidationError(
                'Only staff users can modify existing inventory items.',
                code='invalid'
            )

    def validate_warn_limit(self):
        """
        Ensure that the warn limit of an item cannot be negative.
        """
        if self.warn_limit < 0:
            raise ModelValidationError(
                'The warn limit of an item cannot be a negative value.',
                code='invalid'
            )

    def __str__(self):
        return self.beverage_name


class Order(AuditBase):
    """
    This model represents a **Customer** order. An **Order** contains zero or
    more **OrderItem** and has the following states.

    * **CREATED** - This is the default state of a newly CREATED order. An
      order with this state can transition to any other states. Both employees
      and customers can create new orders.
    * **PENDING** - This state represents an order that is complete and waiting
      for review by an employee. An order can only transition to this state
      from the *CREATED* state and can only transition to one of the following
      states: *APPROVED*, *CANCELED* or *REJECTED* from this state. Both
      employees and customers can mark an order as done transitioning it to
      this state.
    * **APPROVED** - This state represents an order that has already been
      reviewed by an employee and okayed for delivery. An order can only
      transition to this state from the *PENDING* state and cannot transition
      into any further states after this. An order can only be approved if it
      contains at least one **OrderItem**. Once an order is approved, all it's
      **OrderItems** are subtracted from the available inventory. Only
      employees can approve an order.
    * **REJECTED** - This state represents an order that has already been
      reviewed by an employee but not okayed for delivery. An order can only
      transition to this state from the *PENDING* state and cannot transition
      into any further states after this. Only employees can reject an order.
    * **CANCELED** - This state represents an order that has been canceled and
      thus should not be considered for further review. An order can only
      transition into this state from either the *CREATED* or *PENDING* states
      but cannot transition into any other further states after this. Both
      employees and customers can cancel an order.

    An **OrderItem** can only be added or updated on an order that is in the
    **CREATED** or **PENDING** state.
    """

    class OrderState(Choices):
        """The different states of an **Order**."""
        APPROVED = ('A', 'APPROVED')
        CANCELED = ('C', 'CANCELED')
        CREATED = ('N', 'CREATED')
        PENDING = ('P', 'PENDING')
        REJECTED = ('R', 'REJECTED')

    STATE_CHANGE_FORBIDDEN_ERROR_MSG: str = (
        'Changing the state of an order from "%(current_state)s" to '
        '"%(new_state)s" is forbidden.'
    )
    ITEM_LIST_MODIFICATION_FORBIDDEN_ERROR_MSG: str = (
        "An order's item list can only be modified while the order is either "
        'in the "CREATED" or "PENDING" state. The current state of the order '
        'is "%s".'
    )

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    state = models.CharField(
        max_length=1,
        choices=OrderState.to_list(),
        default=OrderState.CREATED.choice_value
    )
    handler = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    review_date = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    @property
    def can_update_order_items(self) -> bool:
        """
        Returns *True* if this order's **OrderItems** can be modified or
        added, *False* otherwise. An order's item list can only be updated
        while the order is either in the *CREATED* or *PENDING* state.

        :return: True if this order's items list can be modified,
                 False otherwise.
        """
        return self.is_created or self.is_pending

    @property
    def is_approved(self) -> bool:
        """
        Returns *True* if this order is marked as *APPROVED*, *False*
        otherwise.

        :return: True if this order is marked as APPROVED, False otherwise.
        """
        return self.state == Order.OrderState.APPROVED.choice_value

    @property
    def is_canceled(self) -> bool:
        """
        Returns *True* if this order is marked as *CANCELED*, *False*
        otherwise.

        :return: True if this order is marked as CANCELED, False otherwise.
        """
        return self.state == Order.OrderState.CANCELED.choice_value

    @property
    def is_created(self) -> bool:
        """
        Returns *True* if this order is in the *CREATED* state, *False*
        otherwise.

        :return: True if this order is in the CREATED state, False otherwise.
        """
        return self.state == Order.OrderState.CREATED.choice_value

    @property
    def is_pending(self) -> bool:
        """
        Returns *True* if this order is marked as *PENDING*, *False*
        otherwise.

        :return: True if this order is marked as PENDING, False otherwise.
        """
        return self.state == Order.OrderState.PENDING.choice_value

    @property
    def is_rejected(self) -> bool:
        """
        Returns *True* if this order is marked as *REJECTED*, *False*
        otherwise.

        :return: True if this order is marked as REJECTED, False otherwise.
        """
        return self.state == Order.OrderState.REJECTED.choice_value

    @property
    def total_price(self) -> Decimal:
        """
        Returns the total price of this order.

        :return: the total price of this order.
        """
        total_price: Decimal = ZERO_AMOUNT

        # Calculate the total price
        order_item: OrderItem
        for order_item in self.orderitem_set.all():
            total_price += order_item.total_price

        return total_price

    ##########################################################################
    # ORDER ITEMS LIST MUTATORS
    ##########################################################################
    def add_item(
            self, user: User,
            item: Inventory,
            quantity: int = 1,
            unit_price: Decimal = None) -> OrderItem:
        """
        Creates a new **OrderItem** of the given item, quantity and price and
        adds it to this order. If the provided item is out of stock, this
        method should fail immediately by raising an **OutOfStockError**. An
        **OperationForbiddenError** will also be raised in case this method
        is called on an order that is not on the *CREATED* or *PENDING* state.
        Returns the created **OrderItem**.

        :param user: The user performing this action.
        :param item: The item to include in this order.
        :param quantity: The number of items ordered. Defaults to 1.
        :param unit_price: The price of the item to use. Defaults to the
               current price of the item.

        :return: the created OrderItem instance.

        :raise OperationForbiddenError: If this order is not in the CREATED
               or PENDING state.
        :raise OutOfStockError: if the provided item is out of stock.
        """
        from .exceptions import OutOfStockError, OperationForbiddenError

        # If this order is not in the "CREATED" or "PENDING" state, raise an
        # OperationForbiddenError
        if not self.can_update_order_items:
            raise OperationForbiddenError(
                self.ITEM_LIST_MODIFICATION_FORBIDDEN_ERROR_MSG %
                Order.OrderState.get_choice_display(self.state)
            )

        # If the given item is out of stock raise an OutOfStockError
        if item.is_out_of_stock:
            raise OutOfStockError(item=item)

        # Create and return the created OrderItem
        return OrderItem.objects.create(
            creator=user,
            order=self,
            item=item,
            quantity=quantity,
            unit_price=unit_price or item.price
        )

    def remove_item(self, item: Inventory) -> OrderItem:
        """
        Given an item in this order's item list, remove the item from this
        order's item list. An **OperationForbiddenError** will be raised in
        case this method is called on an order that is not on the *CREATED*
        or *PENDING* state. If the given item is not part of this order's item
        list, then an **ItemNotInOrderError** is raised. Returns the
        **OrderItem** instance of the deleted item.

        :param item: The item to remove from this order's item list.

        :return: The OrderItem instance of the removed item.

        :raise ItemNotInOrderError: If the given item is not part of this
               order's item list.
        :raise OperationForbiddenError: If this order is not in the CREATED
               or PENDING state.
        """
        from .exceptions import ItemNotInOrderError, OperationForbiddenError

        # If this order is not in the "CREATED" or "PENDING" state, raise an
        # OperationForbiddenError
        if not self.can_update_order_items:
            raise OperationForbiddenError(
                self.ITEM_LIST_MODIFICATION_FORBIDDEN_ERROR_MSG %
                Order.OrderState.get_choice_display(self.state)
            )

        # If the given item is not part of this order's item list, raise an
        # ItemNotInOrderError
        if not self.has_item(item):
            raise ItemNotInOrderError(item, self)

        # Get the item's associated "OrderItem" and delete it
        order_item: OrderItem = self.get_item(item)
        order_item.delete()

        # Return the deleted OrderItem
        return order_item

    def update_item(
            self, user: User,
            item: Inventory,
            quantity: int = None,
            unit_price: Decimal = None) -> OrderItem:
        """
        Given an item in this order's item list, update it's details to match
        the given quantity and unit price. An **OperationForbiddenError** will
        be raised in case this method is called on an order that is not on the
        *CREATED* or *PENDING* state. If the given item is not part of this
        order's item list, then an **ItemNotInOrderError** is raised. Returns
        the updated **OrderItem**.

        :param user: The user performing the update.
        :param item: The item in this order's item list that is to be updated.
        :param quantity: The new quantity to set. If not given, the old value
               is used.
        :param unit_price: The new unit price to set. If not given, the old
               value is used.

        :return: the updated OrderItem instance.

        :raise ItemNotInOrderError: If the given item is not part of this
               order's item list.
        :raise OperationForbiddenError: If this order is not in the CREATED
               or PENDING state.
        """
        from .exceptions import ItemNotInOrderError, OperationForbiddenError

        # If this order is not in the "CREATED" or "PENDING" state, raise an
        # OperationForbiddenError
        if not self.can_update_order_items:
            raise OperationForbiddenError(
                self.ITEM_LIST_MODIFICATION_FORBIDDEN_ERROR_MSG %
                Order.OrderState.get_choice_display(self.state)
            )

        # If the given item is not part of this order's item list, raise an
        # ItemNotInOrderError
        if not self.has_item(item):
            raise ItemNotInOrderError(item, self)

        # Get the item's order details
        order_item: OrderItem = self.get_item(item)

        # Update and return the updated order item
        # noinspection PyTypeChecker
        return order_item.update(
            user,
            quantity=quantity or order_item.quantity,
            unit_price=unit_price or order_item.unit_price
        )

    ##########################################################################
    # ORDER ITEMS LIST ACCESSORS
    ##########################################################################
    def get_item(self, item: Inventory) -> Optional[OrderItem]:
        """
        Returns the **OrderItem** of the given item if it is in this order's
        item list. If not returns *None*.

        :param item: The item whose data we want.

        :return: The given item's data or None if the given item is not part
                 of this order's item list.
        """
        return self.orderitem_set.filter(item=item).first()

    def has_item(self, item: Inventory) -> bool:
        """
        Returns *True* if the given **Inventory** item is part of this order's
        item list, otherwise returns *False*.

        :return: True if the given item is part of this order's item list,
                 False otherwise.
        """
        return self.orderitem_set.filter(item=item).exists()

    ##########################################################################
    # ORDER STATE MUTATORS
    ##########################################################################
    def approve(self, employee: Employee, comments: str = None) -> None:
        """
        Marks this order as approved and ready for delivery to the customer by
        changing it's state to *APPROVED*. An order can only change to the
        *APPROVED* state from the *PENDING* state. Therefore if this order is
        not in the *PENDING* state, then an **OperationForbiddenError** will
        be raised.

        A stock deduction of each item in this order's item list is also
        performed. If there isn't enough stock in any of the items in this
        order's item list to satisfy the order, then a
        **NotEnoughStockError** will be raised.

        If this order's item list is empty, i,e has no associated
        **OrderItems**, then an **OrderEmptyError** will be raised.

        **NOTE:** This is the only method in this class that results in any
        stock adjustments.

        :param employee: The employee approving this order.
        :param comments: Optional remarks regarding this approval.

        :raise NotEnoughStockError: If there isn't enough stock in any of the
               items in this order's item list to satisfy the order.
        :raise OperationForbiddenError: If this order is not in the PENDING
               state.
        :raise OrderEmptyError: If this order has no associated OrderItems.
        """
        from .exceptions import OperationForbiddenError, OrderEmptyError

        # If order is not in the "PENDING" state, raise an
        # OperationForbiddenError
        if not self.is_pending:
            raise OperationForbiddenError(
                self.STATE_CHANGE_FORBIDDEN_ERROR_MSG % {
                    'current_state': Order.OrderState.get_choice_display(
                        self.state
                    ),
                    'new_state': Order.OrderState.APPROVED.choice_display
                }
            )

        # If the order's item list is empty, raise an OrderEmptyError
        if not self.orderitem_set.exists():
            raise OrderEmptyError(
                self,
                'An order with no associated OrderItems cannot be '
                'approved.'
            )

        # Perform db mutations in a transaction
        with transaction.atomic():
            # Adjust the stock of each item in the order's item list
            order_item: OrderItem
            for order_item in self.orderitem_set.all():
                item: Inventory = order_item.item
                item.deduct(employee.user, order_item.quantity)

            # Mark this order as approved
            self.update(
                employee.user,
                comments=comments,
                handler=employee,
                review_date=now(),
                state=Order.OrderState.APPROVED.choice_value
            )

    def cancel(self, user: User, comments: str = None) -> None:
        """
        Marks this order as canceled by changing it's state to *CANCELED*. An
        order can only change to the *CANCELED* state from either the
        *CREATED* or *PENDING* state. Therefore calling this method while the
        order is in any other state will result in an
        **OperationForbiddenError** being raised. An optional comment
        describing the reasons for cancellation can be provided.

        :param user: The user performing this operation.
        :param comments: Optional remarks regarding the cancellation.

        :raise OperationForbiddenError: If this order is not in the CREATED or
               PENDING state.
        """
        from .exceptions import OperationForbiddenError

        # If order is not in the "CREATED" or "PENDING" state, raise an
        # OperationForbiddenError
        if not (self.is_created or self.is_pending):
            raise OperationForbiddenError(
                self.STATE_CHANGE_FORBIDDEN_ERROR_MSG % {
                    'current_state': Order.OrderState.get_choice_display(
                        self.state
                    ),
                    'new_state': Order.OrderState.CANCELED.choice_display
                }
            )

        # Update the order to "PENDING" state
        self.update(
            user,
            comments=comments,
            state=Order.OrderState.CANCELED.choice_value
        )

    def mark_ready_for_review(self, user: User) -> None:
        """
        Marks this order as ready for review by changing it's state to
        *PENDING*. An order can only change to the *PENDING* state from the
        *CREATED* state so if this order is not in the *CREATED* state, then
        an **OperationForbiddenError** will be raised.

        If this order's item list is empty, i,e has no associated
        **OrderItems**, then an **OrderEmptyError** will also be raised.

        :param user: The user performing this operation.

        :raise OperationForbiddenError: If this order is not in the CREATED
               state.
        :raise OrderEmptyError: If this order has no associated OrderItems.
        """
        from .exceptions import OperationForbiddenError, OrderEmptyError

        # If order is not in the "CREATED" state, raise an
        # OperationForbiddenError
        if not self.is_created:
            raise OperationForbiddenError(
                self.STATE_CHANGE_FORBIDDEN_ERROR_MSG % {
                    'current_state': Order.OrderState.get_choice_display(
                        self.state
                    ),
                    'new_state': Order.OrderState.PENDING.choice_display
                }
            )

        # If the order's item list is empty, raise an OrderEmptyError
        if not self.orderitem_set.exists():
            raise OrderEmptyError(
                self,
                'An order must contain at least one Order item before it '
                'can be marked as "PENDING".'
            )

        # Update the order to "PENDING" state
        self.update(user, state=Order.OrderState.PENDING.choice_value)

    def reject(self, employee: Employee, comments: str) -> None:
        """
        Marks this order as rejected by changing it's state to *REJECTED*. An
        order can only change to the *REJECTED* state from the *PENDING*
        state. Therefore, if this order is not in the *PENDING* state when
        this method is called, then an **OperationForbiddenError** will be
        raised. The employee making the rejection must provide comments as to
        why he/she is making the rejection.

        :param employee: The employer performing this action.
        :param comments: Remarks regarding the rejection. Non optional.

        :raise OperationForbiddenError: If this order is not in the PENDING
               state.
        """
        from .exceptions import OperationForbiddenError

        # If order is not in the "PENDING" state, raise an
        # OperationForbiddenError
        if not self.is_pending:
            raise OperationForbiddenError(
                self.STATE_CHANGE_FORBIDDEN_ERROR_MSG % {
                    'current_state': Order.OrderState.get_choice_display(
                        self.state
                    ),
                    'new_state': Order.OrderState.REJECTED.choice_display
                }
            )

        # Mark this order as rejected
        self.update(
            employee.user,
            comments=comments,
            handler=employee,
            review_date=now(),
            state=Order.OrderState.REJECTED.choice_value
        )

    def validate_created_by(self):
        """
        Ensure that only admin/staff users or the user instance associated with
        an order's customer can add the order.
        """
        creator: Optional[User] = getattr(self, 'created_by', None)
        customer: Optional[Customer] = getattr(self, 'customer', None)

        # If a "creator" has been provided, then the value must be a staff user
        # or the user instance associated with this order's customer.
        if creator and customer and not creator.is_staff and \
                creator != customer.user:
            raise ModelValidationError(
                'Only staff users or the customer to be associated with this '
                'order can add the order.',
                code='invalid'
            )

    def validate_updated_by(self):
        """
        Ensure that only admin/staff users or the user instance associated with
        an order's customer can modify the order's details.
        """
        modifier: Optional[User] = getattr(self, 'updated_by', None)
        customer: Optional[Customer] = getattr(self, 'customer', None)

        # If a "modifier" has been provided, then the value must be a staff
        # user or the user instance associated with this order's customer.
        if modifier and customer and not modifier.is_staff and \
                modifier != customer.user:
            raise ModelValidationError(
                "Only staff users or the user associated with an order's "
                "customer can modify the order's details.",
                code='invalid'
            )

    def __str__(self):
        return f'{self.customer.name}:{self.get_state_display()}'


class OrderItem(AuditBase):
    """
    This model represents an item(beverage) in the **Inventory** that has been
    included as part of an **Order**.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Inventory, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=ZERO_AMOUNT
    )
    # Manager
    objects = OrderItemManager()

    @property
    def total_price(self) -> Decimal:
        """
        Return the total price of this order entry which is the product of the
        unit price of the item and the quantity ordered.

        :return: the total price of this this order entry.
        """
        return self.unit_price * self.quantity

    def update(self, modifier: User = None, **kwargs) -> AuditBase:
        """
        Extend update and prevent non-staff users from being able to change the
        unit price of an order item. If the user making this update is a
        non-staff user, ignore modification of the ``unit_price`` property.

        :param modifier: The user who initiated the update action/request.
        :param kwargs: A dict of the fields names and their values to update
               this instance with.

        :return: the updated instance.
        """
        if modifier is None or not modifier.is_staff:
            kwargs.pop('unit_price', None)

        return super().update(modifier, **kwargs)

    def validate_created_by(self):
        """
        Ensure that only admin/staff users or the user instance associated with
        an order's customer can add an order-item to the order.
        """
        creator: Optional[User] = getattr(self, 'created_by', None)
        order: Optional[Order] = getattr(self, 'order', None)

        # If a "creator" has been provided, then the value must be a staff user
        # or the user instance associated with this order-item's customer.
        if creator and order and not creator.is_staff and \
                creator != order.customer.user:
            raise ModelValidationError(
                'Only staff users or the customer to be associated with an '
                "order-item's order can add the order-item.",
                code='invalid'
            )

    def validate_updated_by(self):
        """
        Ensure that only admin/staff users or the user instance associated with
        an order's customer can modify the order's order-items.
        """
        modifier: Optional[User] = getattr(self, 'updated_by', None)
        order: Optional[Order] = getattr(self, 'order', None)

        # If a "modifier" has been provided, then the value must be a staff
        # user or the user instance associated with this order-item's customer.
        if modifier and order and not modifier.is_staff and \
                modifier != order.customer.user:
            raise ModelValidationError(
                'Only staff users or the customer associated with an '
                "order-item's order can modify the order-item's details.",
                code='invalid'
            )

    def __str__(self):
        return f'{self.order} | {self.item}'

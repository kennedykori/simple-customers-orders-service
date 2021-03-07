from __future__ import annotations
from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models, transaction
from django.utils.timezone import now

from ..core.enums import Choices
from ..core.models import AuditBase, AuditBaseManager

# Constants

User = get_user_model()

ZERO_AMOUNT = Decimal('0.00')


# Managers

class CustomerManager(AuditBaseManager):
    """
    Manager for the **Customer** model.
    """

    def create(self, creator: User = None, *args, **kwargs) -> Customer:
        """
        Creates a new **Customer** with the given properties and by the given
        creator. The user property given must be a non-staff user, otherwise,
        a **ValueError** will be raised.Returns the created customer instance.

        :param creator: The user who initiated this create/request.
        :param args: Positional arguments to use when creating the customer
                     instance.
        :param kwargs: Key word arguments to use when creating the customer
                       instance.

        :return: the created customer instance.

        :raise ValueError: If the user property given is missing or is a staff
                           user.
        """
        user: Optional[User] = kwargs.get('user', None)

        # If the user property is missing or is a staff user, raise ValueError
        if not user:
            raise ValueError(
                'You must provide the "user" property as a keyword argument'
            )
        elif user.is_staff:
            raise ValueError('The "user" property must be a non staff user.')

        return super().create(creator, *args, **kwargs)


class EmployeeManager(AuditBaseManager):
    """
    Manager for the **Employee** model.
    """

    def create(self, creator: User = None, *args, **kwargs) -> Employee:
        """
        Creates a new **Employee** with the given properties and by the given
        creator. The user property given must be a staff user, otherwise, a
        **ValueError** will be raised. Also, only staff members can add new
        employees. Therefore if the  *creator* argument is provided, the value
        must be a staff user or else a **ValueError** will be raised. Returns
        the created employee instance.

        :param creator: The user who initiated this create/request.
        :param args: Positional arguments to use when creating the employee
                     instance.
        :param kwargs: Key word arguments to use when creating the employee
                       instance.

        :return: the created employee instance.

        :raise ValueError: If the user property given is missing or is a
                           non-staff user. Also if the creator property given
                           is not None and contains a non-staff user.
        """
        # If the creator argument is not None and is a non-staff user, raise
        # ValueError
        if creator and not creator.is_staff:
            raise ValueError(
                'Only staff members can add new employees, "creator" must be '
                'a staff user.'
            )

        # Get the user property from the provided keyword arguments
        user: Optional[User] = kwargs.get('user', None)

        # If the user property is missing or is a non-staff user, raise
        # ValueError
        if not user:
            raise ValueError(
                'You must provide the "user" property as a keyword argument'
            )
        elif not user.is_staff:
            raise ValueError('The "user" property must be a staff user.')

        return super().create(creator, *args, **kwargs)


class InventoryManager(AuditBaseManager):
    """
    Manager for the **Inventory** model.
    """

    def create(self, creator: User = None, *args, **kwargs) -> Inventory:
        """
        Creates a new **Inventory** with the given properties and by the given
        creator. Only staff members can add new inventory items. Therefore if
        the  *creator* argument is provided, the value must be a staff user or
        else a **ValueError** will be raised. Returns the created inventory
        item instance.

        :param creator: The user who initiated this create/request.
        :param args: Positional arguments to use when creating the inventory
                     item.
        :param kwargs: Key word arguments to use when creating the inventory
                       item.

        :return: the created inventory item.

        :raise ValueError: If the creator property given is not None and
                           contains a non-staff user.
        """
        # If the creator argument is not None and is a non-staff user, raise
        # ValueError
        if creator and not creator.is_staff:
            raise ValueError(
                'Only staff members can add new inventory items, "creator" '
                'must be a staff user.'
            )

        return super().create(creator, *args, **kwargs)


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
    # Manager
    objects = CustomerManager()

    def make_order(self) -> Order:
        """
        Creates and returns a new **Order** for this **Customer**.

        :return: the newly created Order instance.
        """
        return Order.objects.create(self.user, customer=self)

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
        default='M'
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    # Manager
    objects = EmployeeManager()

    def __str__(self):
        return self.name


class Inventory(AuditBase):
    """
    This model represents all the items(beverages) offered by the beverage
    shop.
    """

    class BeverageTypes(Choices):
        """
        The different types of beverages in the shop.
        """
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
        default='C'
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
    # Manager
    objects = InventoryManager()

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
            return Inventory.InventoryItemState.get_choice_name('O')
        elif self.is_few_remaining:
            return Inventory.InventoryItemState.get_choice_name('F')
        # For the default case, return AVAILABLE
        return Inventory.InventoryItemState.get_choice_name('A')

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
        """
        The different states of an **Order**.
        """
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
        default='N'
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
        return self.state == Order.OrderState.get_value('APPROVED')

    @property
    def is_canceled(self) -> bool:
        """
        Returns *True* if this order is marked as *CANCELED*, *False*
        otherwise.

        :return: True if this order is marked as CANCELED, False otherwise.
        """
        return self.state == Order.OrderState.get_value('CANCELED')

    @property
    def is_created(self) -> bool:
        """
        Returns *True* if this order is in the *CREATED* state, *False*
        otherwise.

        :return: True if this order is in the CREATED state, False otherwise.
        """
        return self.state == Order.OrderState.get_value('CREATED')

    @property
    def is_pending(self) -> bool:
        """
        Returns *True* if this order is marked as *PENDING*, *False*
        otherwise.

        :return: True if this order is marked as PENDING, False otherwise.
        """
        return self.state == Order.OrderState.get_value('PENDING')

    @property
    def is_rejected(self) -> bool:
        """
        Returns *True* if this order is marked as *REJECTED*, *False*
        otherwise.

        :return: True if this order is marked as REJECTED, False otherwise.
        """
        return self.state == Order.OrderState.get_value('REJECTED')

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
    # ORDER ITEM LIST MUTATORS
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
                Order.OrderState.get_choice_name(self.state)
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
                Order.OrderState.get_choice_name(self.state)
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
                Order.OrderState.get_choice_name(self.state)
            )

        # If the given item is not part of this order's item list, raise an
        # ItemNotInOrderError
        if not self.has_item(item):
            raise ItemNotInOrderError(item, self)

        # Get the item's order details
        order_item: OrderItem = self.get_item(item)

        # Update and return the updated order item
        return order_item.update(
            user,
            quantity=quantity or order_item.quantity,
            unit_price=unit_price or order_item.unit_price
        )

    ##########################################################################
    # ORDER ITEM LIST ACCESSORS
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
        return (item.pk,) in self.orderitem_set.values_list('item')

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
                    'current_state': Order.OrderState.get_choice_name(
                        self.state
                    ),
                    'new_state': Order.OrderState.get_choice_name(
                        Order.OrderState.get_value('APPROVED')
                    )
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
                state=Order.OrderState.get_value('APPROVED')
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
                    'current_state': Order.OrderState.get_choice_name(
                        self.state
                    ),
                    'new_state': Order.OrderState.get_choice_name(
                        Order.OrderState.get_value('CANCELED')
                    )
                }
            )

        # Update the order to "PENDING" state
        self.update(
            user,
            comments=comments,
            state=Order.OrderState.get_value('CANCELED')
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
                    'current_state': Order.OrderState.get_choice_name(
                        self.state
                    ),
                    'new_state': Order.OrderState.get_choice_name(
                        Order.OrderState.get_value('PENDING')
                    )
                }
            )

        # If the order's item list is empty, raise an OrderEmptyError
        if not self.orderitem_set.exists():
            raise OrderEmptyError(
                self,
                'An order should contain at least one Order item before it '
                'can be marked as "PENDING".'
            )

        # Update the order to "PENDING" state
        self.update(user, state=Order.OrderState.get_value('PENDING'))

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
                    'current_state': Order.OrderState.get_choice_name(
                        self.state
                    ),
                    'new_state': Order.OrderState.get_choice_name(
                        Order.OrderState.get_value('REJECTED')
                    )
                }
            )

        # Mark this order as rejected
        self.update(
            employee.user,
            comments=comments,
            handler=employee,
            review_date=now(),
            state=Order.OrderState.get_value('REJECTED')
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

    @property
    def total_price(self) -> Decimal:
        """
        Return the total price of this order entry which is the unit price of
        the item ordered multiplied by the quantity ordered.

        :return: the total price of this this order entry.
        """
        return self.unit_price * self.quantity

    def __str__(self):
        return f'{self.order} | {self.item}'

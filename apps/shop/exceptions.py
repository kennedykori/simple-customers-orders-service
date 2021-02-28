from __future__ import annotations


# Exceptions

class ItemNotInOrderError(Exception):
    """
    An error raised to indicate that a given **Inventory** item is not part of
    an order's item list.
    """
    from .models import Inventory, Order

    item: Inventory = None
    order: Order = None
    message: str = 'The item "%(item)s" is not part of "%(order)s" item list.'

    def __init__(self, item: Inventory, order: Order, message: str = None):
        self.item = item
        self.order = order
        self.message = message or self.message % {
            'item': self.item,
            'order': self.order
        }
        super().__init__(self.message)


class NotEnoughStockError(Exception):
    """
    An error raised to indicate that an **Order** or stock adjustment on an
    **Inventory** item can not be completed as is because of insufficient
    stock.
    """
    from .models import Inventory

    item: Inventory = None
    adjustment_amount: int = 0
    message: str = (
        'The current stock, "%(current_stock)d" of item, "%(item)s" is not '
        'enough for a deduction by "%(adjustment)d" units.'
    )

    def __init__(
            self, item: Inventory,
            adjustment_amount:
            int, message: str = None):
        self.item = item
        self.adjustment_amount = adjustment_amount
        self.message = message or self.message % {
            'adjustment': self.adjustment_amount,
            'current_stock': self.item.on_hand,
            'item': self.item
        }
        super().__init__(self.message)


class OperationForbiddenError(Exception):
    """
    An error raised to indicate that a given operation cannot be performed on
    an object either because the object is in an invalid state or because the
    operation would result's in the object's invariants being broken.
    """

    def __init__(self, message: str):
        super().__init__(message)


class OrderEmptyError(Exception):
    """
    An error raised to indicate that a given operation on an **Order** cannot
    be performed because the order has no associated **OrderItems**, i,e the
    order's item list is empty.
    """
    from .models import Order

    order: Order = None
    message: str = 'The order, "%s" has no associated order items'

    def __init__(self, order: Order, message: str = None):
        self.order = order
        self.message = message or self.message % self.order
        super().__init__(self.message)


class OutOfStockError(Exception):
    """
    An error raised to indicate that an **Order** can not be full filled
    because the stock of an item in the **Order** has been depleted.
    """
    from .models import Inventory

    item: Inventory = None
    message: str = 'The item "%s" is out of stock'

    def __init__(self, item: Inventory, message: str = None):
        self.item = item
        self.message = message or self.message % self.item
        super().__init__(self.message)

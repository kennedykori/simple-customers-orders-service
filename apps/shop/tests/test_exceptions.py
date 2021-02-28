from unittest import TestCase

from ..exceptions import (
    ItemNotInOrderError,
    NotEnoughStockError,
    OrderEmptyError,
    OutOfStockError
)
from ..models import Inventory, Order

from .factories import InventoryFactory, OrderFactory


# TestCases

class ItemNotInOrderErrorTests(TestCase):
    """
    Tests for the **ItemNotInOrderError** class.
    """

    def test_correct_object_creation(self) -> None:
        # Dummy test objects
        item: Inventory = InventoryFactory.build()
        order: Order = OrderFactory.build()

        # Error instances
        err = ItemNotInOrderError(item, order)
        err2 = ItemNotInOrderError(
            InventoryFactory.build(),
            OrderFactory.build(),
            'The given order is empty'
        )

        # Assert that the err instance was initialized correctly
        self.assertIs(err.item, item)
        self.assertIs(err.order, order)
        self.assertEqual(
            err.message,
            'The item "%(item)s" is not part of "%(order)s" item list.' % {
                'item': item,
                'order': order
            }
        )

        self.assertEqual(err2.message, 'The given order is empty')


class NotEnoughStockErrorTests(TestCase):
    """
    Tests for the **NotEnoughStockError** class.
    """

    def test_correct_object_creation(self) -> None:
        # Dummy Test objects
        item: Inventory = InventoryFactory.build(on_hand=10)
        item2: Inventory = InventoryFactory.build(on_hand=50)
        amount, amount2 = 50, 100

        # Error instances
        err = NotEnoughStockError(item, amount)
        err2 = NotEnoughStockError(item2, amount2, 'Insufficient stock')

        # Assert that the error instances were initialized correctly
        self.assertIs(err.item, item)
        self.assertEqual(err.adjustment_amount, amount)
        self.assertEqual(
            err.message,
            (
                'The current stock, "%(current_stock)d" of item, "%(item)s" '
                'is not enough for a deduction by "%(adjustment)d" units.'
            ) % {
                'adjustment': amount,
                'current_stock': 10,
                'item': item
            }
        )

        self.assertIs(err2.item, item2)
        self.assertEqual(err2.adjustment_amount, amount2)
        self.assertEqual(err2.message, 'Insufficient stock')


class OrderEmptyErrorTests(TestCase):
    """
    Tests for the **OrderEmptyError** class.
    """

    def test_correct_object_creation(self) -> None:
        # Dummy test objects
        order: Order = OrderFactory.build()
        order2: Order = OrderFactory.build()

        # Error instances
        err = OrderEmptyError(order)
        err2 = OrderEmptyError(
            order2,
            'The given order has an empty item list'
        )

        # Assert that the error instances were initialized correctly
        self.assertIs(err.order, order)
        self.assertEqual(
            err.message,
            'The order, "%s" has no associated order items' % order
        )

        self.assertIs(err2.order, order2)
        self.assertEqual(
            err2.message,
            'The given order has an empty item list'
        )


class OutOfStockErrorTests(TestCase):
    """
    Tests for the **OutOfStockError** class.
    """

    def test_correct_object_creation(self) -> None:
        # Dummy test objects
        item: Inventory = InventoryFactory.build(no_stock=True)
        item2: Inventory = InventoryFactory.build(no_stock=True)

        # Error instances
        err = OutOfStockError(item)
        err2 = OutOfStockError(item2, 'The given item is out of stock')

        # Assert that the error instances were initialized correctly
        self.assertIs(err.item, item)
        self.assertEqual(
            err.message,
            'The item "%s" is out of stock' % item
        )

        self.assertIs(err2.item, item2)
        self.assertEqual(err2.message, 'The given item is out of stock')

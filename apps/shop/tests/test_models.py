from decimal import Decimal
from typing import List

from django.contrib.auth import get_user_model

from ...core.exceptions import ModelValidationError
from ...core.tests.factories import AdminFactory, UserFactory
from ...core.tests.test_models import AuditBaseTestCase

from ..exceptions import (
    ItemNotInOrderError,
    NotEnoughStockError,
    OperationForbiddenError,
    OrderEmptyError,
    OutOfStockError
)
from ..models import (
    ZERO_AMOUNT,
    Customer,
    Employee,
    Inventory,
    Order,
    OrderItem
)

from .factories import (
    CustomerFactory,
    EmployeeFactory,
    InventoryFactory,
    OrderFactory,
    OrderItemFactory
)

# TODO: Should probably check than validation of non-editable fields is enabled
#  before performing tests that depend on a model's non-editable fields being
#  valid


# Helpers

User = get_user_model()


# TestCases

class CustomerTests(AuditBaseTestCase):
    """
    Tests for the ``Customer`` model.
    """

    def setUp(self) -> None:
        self.staff: User = AdminFactory.create()
        self.user: User = UserFactory.create()
        self.user2: User = UserFactory.create()
        self.user3: User = UserFactory.create()
        self.customer: Customer = CustomerFactory.create(
            created_by=self.user2,
            user=self.user2
        )

    def test_correct_object_creation(self) -> None:
        """
        Assert that ``Customer.objects.create()`` method creates the expected
        value.
        """
        # Create customer object
        customer: Customer = Customer.objects.create(
            self.user,
            address='An address',
            name='First_name Second_name',
            phone_number='+254722000000',
            user=self.user
        )

        # Assert that the created customer has the correct details
        self.assertEqual(customer.address, 'An address')
        self.assertEqual(customer.created_by, self.user)
        self.assertEqual(customer.name, 'First_name Second_name')
        self.assertEqual(customer.phone_number, '+254722000000')
        self.assertIsNone(customer.updated_by)
        self.assertEqual(customer.user, self.user)

    def test_creation_by_a_non_admin_non_owning_user_fails(self) -> None:
        """
        Assert that only staff/admin users or the user instance to be
        associated with the customer object to be created can create the
        object.
        """
        # Assert that only admin/staff users or the user instance associated
        # with the customer to be created can add the customer.
        with self.assertRaises(ModelValidationError) as cm:
            Customer.objects.create(
                self.user,  # Should be `user3` or any admin user
                address='An address',
                name='First_name Second_name',
                phone_number='+254722000000',
                user=self.user3
            )
        self.assertIn('created_by', cm.exception.message_dict)
        self.assertIn(
            'Only staff users or the user to be associated with the customer '
            'can add the customer.',
            cm.exception.message_dict.get('created_by')
        )

    def test_creation_with_missing_user_value_fails(self) -> None:
        """
        Assert that a value must be provided for the user property when
        creating a new customer object.
        """
        # Assert that the user property must be provided when creating a
        # customer instance
        with self.assertRaises(ModelValidationError) as cm:
            Customer.objects.create(
                self.user,
                address='An address',
                name='First_name Second_name',
                phone_number='+254722000000',
                # user=user  # Missing value
            )
        self.assertIn('user', cm.exception.message_dict)
        self.assertIn(
            'Please provide the user instance associated with this customer.',
            cm.exception.message_dict.get('user')
        )

    def test_creation_with_an_admin_user_fails(self) -> None:
        """
        Assert than the value given for the `user` property when creating a
        customer object *must not* be a staff/admin user.
        """
        # Assert that a customer's user property cannot be a staff user
        with self.assertRaises(ModelValidationError) as cm:
            CustomerFactory.create(created_by=self.staff, user=self.staff)
        self.assertIn('user', cm.exception.message_dict)
        self.assertIn(
            'The user instance provided must be a non-staff user.',
            cm.exception.message_dict.get('user')
        )

    def test_make_order(self) -> None:
        """
        Assert that the ``Customer.make_order()`` method works as expected.
        """
        # Make order
        order: Order = self.customer.make_order()

        # Assert that the created order has the correct details
        self.assertIsNotNone(order)
        self.assertEqual(order.created_by, self.customer.user)
        self.assertEqual(order.customer, self.customer)
        self.assertTrue(order.is_created)

    def test_str(self) -> None:
        """
        Assert that ``Customer.__str__()`` returns the expected value.
        """
        # Assert that __str__ returns the name of the customer
        self.assertEqual(str(self.customer), self.customer.name)

    def test_update(self) -> None:
        """
        Assert that the ``Customer.update()`` method works as expected.
        """
        # Create customer object
        customer: Customer = Customer.objects.create(
            self.user,
            address='An address',
            name='First_name Second_name',
            phone_number='+254722000000',
            user=self.user
        )

        # Update the object
        customer.update(
            self.staff,
            address='A different address',
            name='First_name Sur_name',
            phone_number='+254722111111'
        )

        # Assert that the customer instance was updated correctly
        customer.refresh_from_db()
        self.assertEqual(customer.address, 'A different address')
        self.assertEqual(customer.created_by, self.user)
        self.assertEqual(customer.name, 'First_name Sur_name')
        self.assertEqual(customer.phone_number, '+254722111111')
        self.assertEqual(customer.updated_by, self.staff)
        self.assertEqual(customer.user, self.user)

    def test_update_by_a_non_admin_non_owing_user_fails(self) -> None:
        """
        Assert that only staff/admin users or the user instance associated with
        a customer can update the customer object.
        """
        # Create customer object
        customer: Customer = Customer.objects.create(
            self.user,
            address='An address',
            name='First_name Second_name',
            phone_number='+254722000000',
            user=self.user
        )

        # Updating the object should fail
        with self.assertRaises(ModelValidationError) as cm:
            customer.update(
                self.user2,
                address='A different address',
                name='First_name Sur_name',
                phone_number='+254722111111'
            )
        self.assertIn('updated_by', cm.exception.message_dict)
        self.assertIn(
            'Only staff users or the user associated with the customer can '
            "modify the customer's details.",
            cm.exception.message_dict.get('updated_by')
        )

        # Assert that the customer instance was not updated
        customer.refresh_from_db()
        self.assertEqual(customer.address, 'An address')
        self.assertEqual(customer.created_by, self.user)
        self.assertEqual(customer.name, 'First_name Second_name')
        self.assertEqual(customer.phone_number, '+254722000000')
        self.assertEqual(customer.user, self.user)
        self.assertIsNone(customer.updated_by)


class EmployeeTests(AuditBaseTestCase):
    """
    Tests for the ``Employee`` model.
    """

    def setUp(self) -> None:
        self.employee: Employee = EmployeeFactory.create()
        self.staff: User = AdminFactory.create()
        self.staff2: User = AdminFactory.create()
        self.user: User = UserFactory.create()

    def test_correct_object_creation(self) -> None:
        """
        Assert that the ``Employee.objects.create()`` method creates the
        expected value.
        """
        # Create employee object
        employee: Employee = Employee.objects.create(
            self.staff,
            name='First_name Second_name',
            user=self.staff
        )

        # Assert that the created employee has the correct details
        self.assertEqual(employee.created_by, self.staff)
        self.assertEqual(employee.name, 'First_name Second_name')
        self.assertEqual(employee.gender, Employee.Gender.MALE.choice_value)
        self.assertIsNone(employee.updated_by)
        self.assertEqual(employee.user, self.staff)

    def test_creation_by_a_non_admin_user_fails(self) -> None:
        """
        Assert that only staff/admin users should be able to add/create new
        employees.
        """
        # Assert that an employee instance cannot be created by a non-staff
        # user
        with self.assertRaises(ModelValidationError) as cm:
            EmployeeFactory.create(created_by=self.user, user=self.staff)
        self.assertIn('created_by', cm.exception.message_dict)
        self.assertIn(
            'Only staff users can add new employees.',
            cm.exception.message_dict.get('created_by')
        )

    def test_creation_with_missing_user_value_fails(self) -> None:
        """
        Assert that a value must be provided for the user property when
        creating a new employee object.
        """
        # Assert that the user property must be provided when creating an
        # employee instance
        with self.assertRaises(ModelValidationError) as cm:
            Employee.objects.create(
                self.staff,
                name='First_name Second_name',
                # user=staff  # Missing value
            )
        self.assertIn('user', cm.exception.message_dict)
        self.assertIn(
            'Please provide the user instance associated with this employee.',
            cm.exception.message_dict.get('user')
        )

    def test_creation_with_a_non_admin_user_fails(self) -> None:
        """
        Assert that the value provided for the user property when creating a
        new employee must be a staff/admin user.
        """
        # Assert that an employee's user property cannot be a non-staff user
        with self.assertRaises(ModelValidationError) as cm:
            EmployeeFactory.create(created_by=self.staff2, user=self.user)
        self.assertIn('user', cm.exception.message_dict)
        self.assertIn(
            'The user instance provided must be a staff user.',
            cm.exception.message_dict.get('user')
        )

    def test_str(self) -> None:
        """
        Assert that ``Employee.__str__()`` returns the expected value.
        """
        # Assert that __str__ returns the name of the employee
        self.assertEqual(str(self.employee), self.employee.name)

    def test_update(self) -> None:
        """
        Assert that ``Employee.update()`` works as expected.
        """
        # Create employee object
        employee: Employee = Employee.objects.create(
            self.staff,
            name='First_name Second_name',
            user=self.staff
        )

        # Update the object
        employee.update(
            self.staff2,
            name='First_name Sur_name',
            gender=Employee.Gender.FEMALE.choice_value
        )

        # Assert that the employee instance was updated correctly
        employee.refresh_from_db()
        self.assertEqual(employee.created_by, self.staff)
        self.assertEqual(employee.name, 'First_name Sur_name')
        self.assertEqual(employee.gender, Employee.Gender.FEMALE.choice_value)
        self.assertEqual(employee.updated_by, self.staff2)
        self.assertEqual(employee.user, self.staff)

    def test_update_by_a_non_admin_user_fails(self) -> None:
        """
        Assert that only admin/staff users can update employee objects.
        """
        # Create employee object
        employee: Employee = Employee.objects.create(
            self.staff,
            name='First_name Second_name',
            user=self.staff
        )

        # Updating the object with a non-staff user should fail
        with self.assertRaises(ModelValidationError) as cm:
            employee.update(
                self.user,
                name='First_name Sur_name',
                gender=Employee.Gender.FEMALE.choice_value
            )
        self.assertIn('updated_by', cm.exception.message_dict)
        self.assertIn(
            'Only staff users can modify existing employees data.',
            cm.exception.message_dict.get('updated_by')
        )

        # Assert that the employee instance was not updated
        employee.refresh_from_db()
        self.assertEqual(employee.created_by, self.staff)
        self.assertEqual(employee.name, 'First_name Second_name')
        self.assertEqual(employee.gender, Employee.Gender.MALE.choice_value)
        self.assertEqual(employee.user, self.staff)
        self.assertIsNone(employee.updated_by)


class InventoryTests(AuditBaseTestCase):
    """
    Tests for the ``Inventory`` model.
    """

    def setUp(self) -> None:
        self.staff: User = AdminFactory.create()
        self.staff2: User = AdminFactory.create()
        self.user: User = UserFactory.create()

    def test_correct_object_creation(self) -> None:
        """
        Assert that ``Inventory.objects.create()`` method creates the expected
        value.
        """
        # Create an inventory object
        beverage: Inventory = Inventory.objects.create(
            self.staff,
            beverage_name='Mocha Java',
            on_hand=1000,
            price=Decimal('6.40'),
            warn_limit=100
        )

        # Assert that the created inventory item has the correct state
        self.assertEqual(beverage.beverage_name, 'Mocha Java')
        self.assertEqual(
            beverage.beverage_type,
            Inventory.BeverageTypes.COFFEE.choice_value
        )
        self.assertFalse(beverage.caffeinated)
        self.assertFalse(beverage.flavored)
        self.assertTrue(beverage.is_available)
        self.assertFalse(beverage.is_few_remaining)
        self.assertFalse(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 1000)
        self.assertEqual(beverage.price, Decimal('6.40'))
        self.assertEqual(
            beverage.state,
            Inventory.InventoryItemState.AVAILABLE.choice_display
        )
        self.assertIsNone(beverage.updated_by)
        self.assertEqual(beverage.warn_limit, 100)

    def test_creation_by_a_non_admin_user_fails(self) -> None:
        """
        Assert that only staff/admin users should be able to add/create new
        employees.
        """
        # Assert that an inventory item cannot be created by a non-staff user
        with self.assertRaises(ModelValidationError) as cm:
            InventoryFactory.create(created_by=self.user)
        self.assertIn('created_by', cm.exception.message_dict)
        self.assertIn(
            'Only staff users can add new inventory items.',
            cm.exception.message_dict.get('created_by')
        )

    def test_creation_with_a_negative_on_hand_value_fails(self) -> None:
        """
        Assert that an inventory item cannot be created with a negative
        `on_hand` value.
        """
        with self.assertRaises(ModelValidationError) as cm:
            Inventory.objects.create(
                self.staff,
                beverage_name='Mocha Java',
                on_hand=-100,
                price=Decimal('6.40'),
                warn_limit=100
            )
        self.assertIn('on_hand', cm.exception.message_dict)
        self.assertIn(
            'The available quantity of an item cannot be a negative value.',
            cm.exception.message_dict.get('on_hand')
        )

    def test_creation_with_a_negative_price_fails(self) -> None:
        """
        Assert that an inventory item cannot be created with a negative price.
        """
        with self.assertRaises(ModelValidationError) as cm:
            Inventory.objects.create(
                self.staff,
                beverage_name='Mocha Java',
                on_hand=1000,
                price=Decimal('-6.50'),
                warn_limit=100
            )
        self.assertIn('price', cm.exception.message_dict)
        self.assertIn(
            'The price of an item cannot be negative.',
            cm.exception.message_dict.get('price')
        )

    def test_creation_with_a_negative_warn_limit_fails(self) -> None:
        """
        Assert that an inventory item cannot be created with a negative
        `warn_limit` value.
        """
        with self.assertRaises(ModelValidationError) as cm:
            Inventory.objects.create(
                self.staff,
                beverage_name='Mocha Java',
                on_hand=1000,
                price=Decimal('6.40'),
                warn_limit=-3
            )
        self.assertIn('warn_limit', cm.exception.message_dict)
        self.assertIn(
            'The warn limit of an item cannot be a negative value.',
            cm.exception.message_dict.get('warn_limit')
        )

    def test_deduct(self) -> None:
        """
        Assert that the ``Inventory.deduct()`` method modifies an items state
        in the expected way.
        """
        # Create an inventory object
        beverage: Inventory = InventoryFactory.create(
            on_hand=1000,
            warn_limit=100
        )

        # Assert we have the expected state before we perform any deductions
        self.assertTrue(beverage.is_available)
        self.assertFalse(beverage.is_few_remaining)
        self.assertFalse(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 1000)
        self.assertEqual(beverage.warn_limit, 100)
        self.assertIsNone(beverage.updated_by)

        # Perform a deduction
        beverage.deduct(self.staff, 950)

        # Assert we have the expected state after the deduction
        self.assertFalse(beverage.is_available)
        self.assertTrue(beverage.is_few_remaining)
        self.assertFalse(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 50)
        self.assertEqual(beverage.updated_by, self.staff)
        self.assertEqual(beverage.warn_limit, 100)

        # Perform another deduction
        beverage.deduct(self.staff2, 50)

        # Assert we have the expected state after the deduction
        self.assertFalse(beverage.is_available)
        self.assertTrue(beverage.is_few_remaining)
        self.assertTrue(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 0)
        self.assertEqual(beverage.updated_by, self.staff2)

    def test_deduction_by_a_negative_quantity_fails(self) -> None:
        """
        Assert that passing a negative quantity to the ``Inventory.deduct()``
        method fails.
        """
        # Create an inventory object
        beverage: Inventory = InventoryFactory.create(
            on_hand=1000,
            warn_limit=100
        )

        # Assert that when a negative quantity is provided, we get an error
        with self.assertRaisesMessage(
                ValueError,
                '"quantity" must be a positive value'):
            beverage.deduct(self.staff, -10)

    def test_deduction_by_more_than_available_stock_fails(self) -> None:
        """
        Assert that any deduction that would result in an item's stock being
        negative results in a `NotEnoughStockError` being raised.
        """
        # Create an inventory object
        beverage: Inventory = InventoryFactory.create(
            on_hand=1000,
            warn_limit=100
        )

        # Assert that attempting to deduct more than the remaining stock will
        # result in a NotEnoughStockError
        with self.assertRaises(NotEnoughStockError):
            beverage.deduct(self.staff, 10_000)

        # Assert that no changes to the item were performed with the above
        # deduction attempt
        self.assertTrue(beverage.is_available)
        self.assertFalse(beverage.is_few_remaining)
        self.assertFalse(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 1000)
        self.assertEqual(beverage.warn_limit, 100)

    def test_state_property(self) -> None:
        """
        Assert that the ``Inventory.state`` property returns the expected
        value.
        """
        # Create an inventory object
        beverage: Inventory = InventoryFactory.create(
            on_hand=1000,
            warn_limit=100
        )

        # Assert that the inventory item is in the expected state
        self.assertEqual(
            beverage.state,
            Inventory.InventoryItemState.AVAILABLE.choice_display
        )
        self.assertTrue(beverage.is_available)

        # Deduct the item stock to a low stock level
        beverage.deduct(self.staff, 950)

        # Assert that the inventory item is in the expected state after the
        # deduction
        self.assertEqual(
            beverage.state,
            Inventory.InventoryItemState.FEW_REMAINING.choice_display
        )
        self.assertTrue(beverage.is_few_remaining)

        # Deduct all remaining item stock
        beverage.deduct(self.staff, 50)

        # Assert that the inventory item is in the expected state after the
        # deduction
        self.assertEqual(
            beverage.state,
            Inventory.InventoryItemState.OUT_OF_STOCK.choice_display
        )
        self.assertTrue(beverage.is_out_of_stock)

    def test_str(self) -> None:
        """
        Assert that the ``Inventory.__str__()`` method returns the expected
        value.
        """
        # Dummy test object
        beverage: Inventory = InventoryFactory.create()

        # Assert that __str__ returns the name of the beverage
        self.assertEqual(str(beverage), beverage.beverage_name)

    def test_update(self) -> None:
        """
        Tests for the **Inventory.update()** method.
        """
        # Create an inventory item
        beverage: Inventory = Inventory.objects.create(
            self.staff,
            beverage_name='Mocha Java',
            on_hand=1000,
            price=Decimal('6.40'),
            warn_limit=100
        )

        # Update the item
        beverage.update(
            self.staff2,
            beverage_name='Vanilla Tea',
            beverage_type=Inventory.BeverageTypes.TEA.choice_value,
            caffeinated=True,
            flavored=True,
            on_hand=0,
            price=Decimal('15.50'),
            warn_limit=10
        )

        # Assert that the inventory item was updated correctly
        self.assertEqual(beverage.beverage_name, 'Vanilla Tea')
        self.assertEqual(
            beverage.beverage_type,
            Inventory.BeverageTypes.TEA.choice_value
        )
        self.assertTrue(beverage.caffeinated)
        self.assertTrue(beverage.flavored)
        self.assertFalse(beverage.is_available)
        self.assertTrue(beverage.is_few_remaining)
        self.assertTrue(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 0)
        self.assertEqual(beverage.price, Decimal('15.50'))
        self.assertEqual(
            beverage.state,
            Inventory.InventoryItemState.OUT_OF_STOCK.choice_display
        )
        self.assertEqual(beverage.created_by, self.staff)
        self.assertEqual(beverage.updated_by, self.staff2)
        self.assertEqual(beverage.warn_limit, 10)

    def test_update_by_a_non_admin_user_fails(self) -> None:
        """
        Assert that only admin/staff users can update inventory objects.
        """
        # Create an inventory item
        beverage: Inventory = Inventory.objects.create(
            self.staff,
            beverage_name='Mocha Java',
            on_hand=1000,
            price=Decimal('6.40'),
            warn_limit=100
        )

        # Updating the object with a non-staff user should fail
        with self.assertRaises(ModelValidationError) as cm:
            beverage.update(
                self.user,
                beverage_name='Vanilla Tea',
                beverage_type=Inventory.BeverageTypes.TEA.choice_value,
                caffeinated=True,
                flavored=True,
                on_hand=0,
                price=Decimal('15.50'),
                warn_limit=10
            )
        self.assertIn('updated_by', cm.exception.message_dict)
        self.assertIn(
            'Only staff users can modify existing inventory items.',
            cm.exception.message_dict.get('updated_by')
        )

        # Assert that the inventory instance was not updated
        beverage.refresh_from_db()
        self.assertEqual(beverage.beverage_name, 'Mocha Java')
        self.assertEqual(
            beverage.beverage_type,
            Inventory.BeverageTypes.COFFEE.choice_value
        )
        self.assertFalse(beverage.caffeinated)
        self.assertFalse(beverage.flavored)
        self.assertTrue(beverage.is_available)
        self.assertFalse(beverage.is_few_remaining)
        self.assertFalse(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 1000)
        self.assertEqual(beverage.price, Decimal('6.40'))
        self.assertEqual(
            beverage.state,
            Inventory.InventoryItemState.AVAILABLE.choice_display
        )
        self.assertIsNone(beverage.updated_by)
        self.assertEqual(beverage.warn_limit, 100)


class OrderTests(AuditBaseTestCase):
    """
    Tests for the ``Order`` model.
    """

    def setUp(self) -> None:
        # Create Employee instances
        self.employee: Employee = EmployeeFactory.create()

        # Create Customer instances
        self.customer: Customer = CustomerFactory.create()

        # Create inventory items
        self.item1: Inventory = InventoryFactory.create(
            on_hand=1000,
            warn_limit=100
        )
        self.item2: Inventory = InventoryFactory.create(
            on_hand=250,
            tea=True,
            warn_limit=100
        )
        self.item3: Inventory = InventoryFactory.create(no_stock=True)
        self.items: List[Inventory] = InventoryFactory.create_batch(5)

        # Create order instances
        self.order: Order = OrderFactory.create()
        self.order1: Order = OrderFactory.create(approved=True)
        self.order2: Order = OrderFactory.create(canceled=True)
        self.order3: Order = OrderFactory.create(pending=True)
        self.order4: Order = OrderFactory.create(rejected=True)

        # Create user instances
        self.staff: User = AdminFactory.create()
        self.user: User = UserFactory.create()

    def test_add_item(self) -> None:
        """Assert that the ``Order.add_item`` method works as expected."""
        # Dummy test objects
        big_price = Decimal('230.15')

        # Get a created order instances
        order: Order = self.order

        # Assert that the order is in the expected state before making any
        # modifications
        self.assertFalse(order.orderitem_set.exists())
        self.assertEqual(order.total_price, ZERO_AMOUNT)

        # Add an item
        order_item = order.add_item(order.customer.user, self.item1, 100)

        # Assert that the order is in the correct state after the addition
        self.assertEqual(order.orderitem_set.count(), 1)
        self.assertEqual(order.total_price, self.item1.price * 100)

        # Assert that the created item entry is in the correct state
        self.assertEqual(order_item.item, self.item1)
        self.assertEqual(order_item.quantity, 100)
        self.assertEqual(order_item.unit_price, self.item1.price)

        # Add another item
        order_item = order.add_item(
            self.staff,
            self.item2,
            150,
            big_price
        )

        # Assert that the order is in the correct state after the addition
        self.assertEqual(order.orderitem_set.count(), 2)
        self.assertEqual(
            order.total_price,
            (self.item1.price * 100) + (big_price * 150)
        )

        # Assert that the created item entry is in the correct state
        self.assertEqual(order_item.item, self.item2)
        self.assertEqual(order_item.quantity, 150)
        self.assertEqual(order_item.unit_price, big_price)

    def test_adding_an_item_while_not_in_the_right_state_fails(self) -> None:
        """
        Assert that an inventory item can only be added to an order while the
        order is in the "CREATED" or "PENDING" state. Otherwise, an
        ``OperationForbiddenError`` should be raised.
        """
        # Assert that adding an item to an order that is neither in the
        # "CREATED" or "PENDING" state fails
        self.assertRaises(
            OperationForbiddenError,
            self.order1.add_item,
            self.order1.customer.user,
            self.item1
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order2.add_item,
            self.order2.customer.user,
            self.item1
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order4.add_item,
            self.order4.customer.user,
            self.item1
        )

    def test_adding_an_out_of_stock_item_fails(self) -> None:
        """
        Assert that an inventory item with no stock can not be added to an
        order as per the specification of the ``Order`` model. Instead, an
        ``OutOfStockError`` should be raised.
        """
        # Assert that adding an out of stock item fails
        with self.assertRaises(OutOfStockError):
            self.order.add_item(self.order.customer.user, self.item3)

        # Assert that no modifications were made to the order
        self.assertFalse(self.order.orderitem_set.exists())
        self.assertEqual(self.order.total_price, ZERO_AMOUNT)

    def test_approve(self) -> None:
        """
        Assert that the ``Order.approve()`` method works as expected.
        """
        # Dummy test objects
        comments: str = 'Approved'

        # Get a created order instances
        order: Order = self.order

        # Assert that the order is in the expected state before making any
        # modifications
        self.assertTrue(order.can_update_order_items)
        self.assertIsNone(order.comments)
        self.assertIsNone(order.handler)
        self.assertFalse(order.is_approved)
        self.assertTrue(order.is_created)
        self.assertIsNone(order.review_date)
        self.assertEqual(order.state, Order.OrderState.CREATED.choice_value)
        self.assertEqual(order.total_price, Decimal('0.00'))

        # Add an item to the order and mark the order as pending
        order.add_item(order.customer.user, self.item1, 50)
        order.mark_ready_for_review(order.customer.user)

        # Add another item to the order
        order.add_item(order.customer.user, self.item2, 200)

        # Assert the inventory items are in the expected state
        self.assertTrue(self.item1.is_available)
        self.assertEqual(self.item1.on_hand, 1000)
        self.assertTrue(self.item2.is_available)
        self.assertEqual(self.item2.on_hand, 250)

        # Approve the order
        order.approve(self.employee, comments)

        # Assert that the order is in the expected state after the approval
        self.assertFalse(order.can_update_order_items)
        self.assertEqual(order.comments, comments)
        self.assertEqual(order.handler, self.employee)
        self.assertTrue(order.is_approved)
        self.assertFalse(order.is_created)
        self.assertIsNotNone(order.review_date)
        self.assertEqual(order.state, Order.OrderState.APPROVED.choice_value)
        self.assertEqual(
            order.total_price,
            (self.item1.price * 50) + (self.item2.price * 200)
        )
        self.assertEqual(order.updated_by, self.employee.user)

        # Assert that the stock was adjusted appropriately during approval
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        self.assertTrue(self.item1.is_available)
        self.assertEqual(self.item1.on_hand, 950)
        self.assertFalse(self.item2.is_available)
        self.assertTrue(self.item2.is_few_remaining)
        self.assertEqual(self.item2.on_hand, 50)

    def test_approving_an_order_while_not_in_the_right_state_fails(self)\
            -> None:
        """
        Assert that an order can only be approved while the order is in the
        "PENDING" state. Otherwise, an ``OperationForbiddenError`` should be
        raised.
        """
        # Dummy test objects
        comments: str = 'Approved'

        # Assert that attempting to approve an order that is not in the
        # "PENDING" fails
        self.assertRaises(
            OperationForbiddenError,
            self.order1.approve,
            self.employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order2.approve,
            self.employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order.approve,
            self.employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order4.approve,
            self.employee,
            comments
        )

    def test_approving_an_empty_order_fails(self) -> None:
        """
        Assert that approving an item with an empty item list fails as per the
        specification of the ``Order`` model. An ``OrderEmptyError`` should be
        raised instead.
        """
        # Get a pending order instances
        order: Order = self.order3

        # The order shouldn't have any items
        self.assertFalse(order.orderitem_set.exists())

        # Assert that approving an order with an empty item list fails
        self.assertRaises(OrderEmptyError, order.approve, self.employee)

        # Assert that the state of the order wasn't changed
        self.assertTrue(order.is_pending)

    def test_approving_an_order_with_more_than_enough_stock_fails(self)\
            -> None:
        """
        Assert that approving an order containing items of more than the
        available stock results in a ``NotEnoughStockError`` being raised.
        """
        # Get a pending order instances
        order: Order = self.order3

        # Add an item to the order
        order.add_item(order.customer.user, self.item2, 300)

        # Assert that approving an order of more than available stock fails
        self.assertRaises(NotEnoughStockError, order.approve, self.employee)

        # Assert that the state of the order wasn't changed
        self.assertTrue(order.is_pending)

    def test_cancel(self) -> None:
        """
        Assert that the ``Order.cancel()`` method works as expected.
        """
        # Get an order in the "CREATED" state
        order: Order = self.order

        # Assert that the order is in the expected state before making any
        # modifications
        self.assertTrue(order.can_update_order_items)
        self.assertIsNone(order.comments)
        self.assertFalse(order.is_canceled)
        self.assertTrue(order.is_created)
        self.assertEqual(order.state, Order.OrderState.CREATED.choice_value)

        # Cancel the order
        order.cancel(order.customer.user, 'Changed my mind')

        # Assert that the order is in the expected state after the
        # cancellation
        self.assertFalse(order.can_update_order_items)
        self.assertEqual(order.comments, 'Changed my mind')
        self.assertTrue(order.is_canceled)
        self.assertFalse(order.is_created)
        self.assertEqual(order.state, Order.OrderState.CANCELED.choice_value)
        self.assertEqual(order.updated_by, order.customer.user)

        # Cancellation of a pending order should not fail
        self.assertTrue(self.order3.is_pending)

        self.order3.cancel(self.order3.customer.user)

        self.assertIsNone(self.order3.comments)
        self.assertTrue(self.order3.is_canceled)
        self.assertEqual(self.order3.updated_by, self.order3.customer.user)

    def test_canceling_an_order_while_not_in_the_right_state_fails(self)\
            -> None:
        """
        Assert that an order can only be canceled while the order is either in
        the "CREATED" or "PENDING" state. Otherwise, an
        ``OperationForbiddenError`` should be raised.
        """
        # Assert that cancellation of orders not in the "CREATED" or "PENDING"
        # state results in an error
        self.assertRaises(
            OperationForbiddenError,
            self.order1.cancel,
            self.order1.customer.user
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order2.cancel,
            self.order2.customer.user
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order4.cancel,
            self.order4.customer.user
        )

    def test_correct_object_creation(self) -> None:
        """
        Assert that the ``Order.objects.create()`` method creates the expected
        value.
        """
        # Dummy test objects
        customer: Customer = CustomerFactory.create()

        # Create an order object
        order: Order = Order.objects.create(customer.user, customer=customer)

        # Assert that the created order instance has the correct state
        self.assertTrue(order.can_update_order_items)
        self.assertIsNone(order.comments)
        self.assertEqual(order.customer, customer)
        self.assertIsNone(order.handler)
        self.assertFalse(order.is_approved)
        self.assertFalse(order.is_canceled)
        self.assertTrue(order.is_created)
        self.assertFalse(order.is_pending)
        self.assertFalse(order.is_rejected)
        self.assertIsNone(order.review_date)
        self.assertEqual(order.state, Order.OrderState.CREATED.choice_value)
        self.assertEqual(order.total_price, Decimal('0.00'))

    def test_creation_by_a_non_admin_non_owning_user_fails(self) -> None:
        """
        Assert that only staff/admin users or the user instance associated
        the customer object to be associated with the order instance to be
        created can create the object.
        """
        # Assert that only admin/staff users or the user instance associated
        # with the customer who will own the order can add the order.
        with self.assertRaises(ModelValidationError) as cm:
            Order.objects.create(
                self.user,  # Should be `self.customer.user` or any admin user
                customer=self.customer
            )
        self.assertIn('created_by', cm.exception.message_dict)
        self.assertIn(
            'Only staff users or the customer to be associated with this '
            'order can add the order.',
            cm.exception.message_dict.get('created_by')
        )

    def test_get_item(self) -> None:
        """
        Assert that the ``Order.get_item()`` method returns the expected value.
        """
        # Add items to an order.
        order_item1: OrderItem = self.order.add_item(self.staff, self.items[0])
        order_item2: OrderItem = self.order.add_item(
            self.staff,
            self.items[1],
            3
        )
        order_item3: OrderItem = self.order.add_item(
            self.staff,
            self.items[2],
            6
        )

        # Assert that `.get_item()` returns the order-items of the items added
        # above.
        self.assertEqual(order_item1, self.order.get_item(self.items[0]))
        self.assertEqual(order_item2, self.order.get_item(self.items[1]))
        self.assertEqual(order_item3, self.order.get_item(self.items[2]))

        # Assert that `get_item()` returns `None` for items not in the order.
        self.assertIsNone(self.order.get_item(self.items[3]))
        self.assertIsNone(self.order.get_item(self.items[4]))

    def test_has_item(self) -> None:
        """
        Assert that the ``Order.has_item()`` method returns the expected value.
        """
        # Add items to an order.
        self.order.add_item(self.staff, self.items[0])
        self.order.add_item(self.staff, self.items[1], 3)
        self.order.add_item(self.staff, self.items[2], 6)

        # Assert that `.has_item()` returns `True` for the items added above.
        self.assertTrue(self.order.get_item(self.items[0]))
        self.assertTrue(self.order.get_item(self.items[1]))
        self.assertTrue(self.order.get_item(self.items[2]))

        # Assert that `has_item()` returns `False` for items not in the order.
        self.assertFalse(self.order.get_item(self.items[3]))
        self.assertFalse(self.order.get_item(self.items[4]))

    def test_mark_ready_for_review(self) -> None:
        """
        Assert that the ``Order.mark_ready_for_review()`` method works as
        expected.
        """
        # Get a created order instances
        order: Order = self.order

        # Assert that the order is in the expected state before making any
        # modifications
        self.assertTrue(order.can_update_order_items)
        self.assertTrue(order.is_created)
        self.assertFalse(order.is_pending)
        self.assertEqual(order.state, Order.OrderState.CREATED.choice_value)

        # Add an item to the order
        order.add_item(order.customer.user, self.item1, 50)

        # Mark the order as "PENDING" and assert that the order is in the
        # expected state
        order.mark_ready_for_review(order.customer.user)
        self.assertTrue(order.can_update_order_items)
        self.assertFalse(order.is_created)
        self.assertTrue(order.is_pending)
        self.assertEqual(order.state, Order.OrderState.PENDING.choice_value)
        self.assertEqual(order.total_price, self.item1.price * 50)
        self.assertEqual(order.updated_by, order.customer.user)

    def test_marking_an_empty_order_as_ready_fails(self) -> None:
        """
        Assert that marking an empty order as ready raises an
        ``OrderEmptyError``.
        """
        # Get a created order instances
        order: Order = self.order

        # Assert that attempting to mark an order with an empty item list as
        # "PENDING" fails
        self.assertRaises(
            OrderEmptyError,
            order.mark_ready_for_review,
            order.customer.user
        )

        # Assert that no modifications were made to the order
        self.assertTrue(order.is_created)
        self.assertEqual(order.orderitem_set.count(), 0)

    def test_marking_an_order_ready_while_not_in_the_right_state_fails(self)\
            -> None:
        """
        Assert that an order can only be marked as ready while the order is in
        the "CREATED" state. Otherwise, an ``OperationForbiddenError`` should
        be raised.
        """
        # Assert that attempting to mark an order that is not in the "CREATED"
        # state as "PENDING" fails
        self.assertRaises(
            OperationForbiddenError,
            self.order1.mark_ready_for_review,
            self.order1.customer.user
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order2.mark_ready_for_review,
            self.order2.customer.user
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order3.mark_ready_for_review,
            self.order3.customer.user
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order4.mark_ready_for_review,
            self.order4.customer.user
        )

    def test_reject(self) -> None:
        """
        Assert that the ``Order.reject()`` method works as expected.
        """
        # Dummy test objects
        comments: str = 'A good reason'
        employee: Employee = EmployeeFactory.create()

        # Get a pending order instances
        order: Order = self.order3

        # Assert that the order is in the expected state before making any
        # modifications
        self.assertTrue(order.can_update_order_items)
        self.assertIsNone(order.comments)
        self.assertIsNone(order.handler)
        self.assertTrue(order.is_pending)
        self.assertFalse(order.is_rejected)
        self.assertIsNone(order.review_date)
        self.assertEqual(order.state, Order.OrderState.PENDING.choice_value)

        # Reject the order
        order.reject(employee, comments)

        # Assert that the order is in the expected state after the rejection
        self.assertFalse(order.can_update_order_items)
        self.assertEqual(order.comments, comments)
        self.assertEqual(order.handler, employee)
        self.assertFalse(order.is_pending)
        self.assertTrue(order.is_rejected)
        self.assertIsNotNone(order.review_date)
        self.assertEqual(order.state, Order.OrderState.REJECTED.choice_value)
        self.assertEqual(order.updated_by, employee.user)

    def test_rejecting_an_order_ready_while_not_in_the_right_state_fails(self)\
            -> None:
        """
        Assert that an order can only be rejected while the order is in the
        "PENDING" state. Otherwise, an ``OperationForbiddenError`` should be
        raised.
        """
        # Dummy test objects
        comments: str = 'A good reason'

        # Assert that attempting to reject an order that is not in the
        # "PENDING" fails
        self.assertRaises(
            OperationForbiddenError,
            self.order1.reject,
            self.employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order2.reject,
            self.employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order.reject,
            self.employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order4.reject,
            self.employee,
            comments
        )

    def test_remove_item(self) -> None:
        """
        Assert that the ``Order.remove_item()`` method works as expected.
        """
        # Add items to an order.
        self.order.add_item(self.staff, self.items[0])
        self.order.add_item(self.staff, self.items[1], 3)
        self.order.add_item(self.staff, self.items[2], 6)

        # Remove an item
        self.order.remove_item(self.items[0])

        # Assert that the item was removed
        self.assertEqual(self.order.orderitem_set.count(), 2)
        self.assertFalse(self.order.has_item(self.items[0]))

        # Remove another item and assert that the item was removed
        self.order.remove_item(self.items[1])
        self.assertEqual(self.order.orderitem_set.count(), 1)
        self.assertFalse(self.order.has_item(self.items[1]))

    def test_removing_a_non_existing_item_fails(self) -> None:
        """
        Assert that attempting to remove an item that is not in the order fails
        by raising an ``ItemNotInOrderError``.
        """
        # Add items to an order.
        self.order.add_item(self.staff, self.items[0])
        self.order.add_item(self.staff, self.items[1], 3)

        # Assert that attempting to remove items that are not in the order
        # fails
        self.assertRaises(
            ItemNotInOrderError,
            self.order.remove_item,
            self.items[2]
        )
        self.assertRaises(
            ItemNotInOrderError,
            self.order.remove_item,
            self.items[3]
        )

        # Assert that no modifications were made to the order
        self.assertEqual(self.order.orderitem_set.count(), 2)

    def test_removing_an_item_while_not_in_the_right_state_fails(self) -> None:
        """
        Assert that an inventory item can only be removed to an order while the
        order is in the "CREATED" or "PENDING" state. Otherwise, an
        ``OperationForbiddenError`` should be raised.
        """
        # Assert that removing an item to an order that is neither in the
        # "CREATED" or "PENDING" state fails
        self.assertRaises(
            OperationForbiddenError,
            self.order1.remove_item,
            self.item1
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order2.remove_item,
            self.item1
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order4.remove_item,
            self.item1
        )

    def test_str(self) -> None:
        """
        Tests for the **Order.__str__()** method.
        """
        # Assert that __str__ returns the customer name and current state of
        # an order
        self.assertEqual(
            str(self.order),
            '%s:%s' % (
                self.order.customer.name, self.order.get_state_display()
            )
        )
        self.assertEqual(
            str(self.order1),
            '%s:%s' % (
                self.order1.customer.name, self.order1.get_state_display()
            )
        )
        self.assertEqual(
            str(self.order2),
            '%s:%s' % (
                self.order2.customer.name, self.order2.get_state_display()
            )
        )
        self.assertEqual(
            str(self.order3),
            '%s:%s' % (
                self.order3.customer.name, self.order3.get_state_display()
            )
        )
        self.assertEqual(
            str(self.order4),
            '%s:%s' % (
                self.order4.customer.name, self.order4.get_state_display()
            )
        )

    def test_update(self) -> None:
        """
        Assert that the ``Order.update()`` method works as expected.
        """
        # Skip for now. The model's mutators should be used to perform any
        # updates on the model's instances
        ...

    def test_update_item(self) -> None:
        """
        Assert that the ``Order.update_item()`` method works as expected.
        """
        # Dummy test objects
        price1 = Decimal('100.00')
        price2 = Decimal('150.75')
        price3 = Decimal('180.25')

        # Add items to an order.
        self.order.add_item(self.staff, self.items[0], unit_price=price1)
        self.order.add_item(self.staff, self.items[1], 3)
        self.order.add_item(self.staff, self.items[2], 6, price2)

        # Assert that we have the expected state after the update
        self.assertEqual(self.order.orderitem_set.count(), 3)
        self.assertEqual(
            self.order.total_price,
            (price1 * 1) + (price2 * 6) + (self.items[1].price * 3)
        )

        # Make an update
        order_item: OrderItem = self.order.update_item(
            self.staff,
            self.items[0],
            10
        )

        # Assert that the update produced the expected results
        self.assertEqual(
            self.order.total_price,
            (price1 * 10) + (price2 * 6) + (self.items[1].price * 3)
        )
        self.assertEqual(order_item.quantity, 10)
        self.assertEqual(order_item.total_price, price1 * 10)

        # Make another update and assert that the results are as expected
        self.order.update_item(self.staff, self.items[1], 2, price3)
        self.assertEqual(
            self.order.total_price,
            (price1 * 10) + (price2 * 6) + (price3 * 2)
        )

    def test_updating_a_non_existing_item_fails(self) -> None:
        """
        Assert that attempting to update an item that is not in the order fails
        by raising an ``ItemNotInOrderError``.
        """
        # Add items to an order.
        self.order.add_item(self.staff, self.items[0])
        self.order.add_item(self.staff, self.items[1], 3)

        # Assert that attempting to update items that are not in the order
        # fails
        self.assertRaises(
            ItemNotInOrderError,
            self.order.update_item,
            self.staff,
            self.items[2],
            2
        )
        self.assertRaises(
            ItemNotInOrderError,
            self.order.update_item,
            self.staff,
            self.items[3],
            5,
            Decimal('60.50')
        )

        # Assert that no modifications were made to the order
        self.assertEqual(
            self.order.total_price,
            self.items[0].price + self.items[1].price * 3
        )

    def test_updating_an_item_while_not_in_the_right_state_fails(self) -> None:
        """
        Assert that an inventory item in an order can only be updated while the
        order is in the "CREATED" or "PENDING" state. Otherwise, an
        ``OperationForbiddenError`` should be raised.
        """
        # Assert that updating an item in an order that is neither in the
        # "CREATED" or "PENDING" state fails
        self.assertRaises(
            OperationForbiddenError,
            self.order1.update_item,
            self.order1.customer.user,
            self.item1,
            6
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order2.update_item,
            self.order2.customer.user,
            self.item1,
            7,
            Decimal('50.00')
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order4.update_item,
            self.order4.customer.user,
            self.item1,
            2
        )

    def test_update_by_a_non_admin_non_owning_user_fails(self) -> None:
        """
        Assert that only staff/admin users or the user instance associated with
        the customer object associated with the order instance to be modified
        can update the order.
        """
        # Assert that only admin/staff users or the user instance associated
        # with the customer who owns the order can update the order.
        with self.assertRaises(ModelValidationError) as cm:
            self.order.cancel(
                # Should be `self.order.customer.user` or any admin user
                self.user,
                self.items[0],
            )
        self.assertIn('updated_by', cm.exception.message_dict)
        self.assertIn(
            "Only staff users or the user associated with an order's "
            "customer can modify the order's details.",
            cm.exception.message_dict.get('updated_by')
        )


class OrderItemTests(AuditBaseTestCase):
    """
    Tests for the ``OrderItem`` model.
    """

    def setUp(self) -> None:
        self.item: Inventory = InventoryFactory.create(price=Decimal('10.50'))
        self.user: User = UserFactory.create()
        self.customer: Customer = CustomerFactory.create(
            created_by=self.user,
            user=self.user
        )
        self.order: Order = OrderFactory.create(
            created_by=self.user,
            customer=self.customer
        )
        self.user2: User = UserFactory.create()
        self.staff: User = AdminFactory.create()

    def test_correct_object_creation(self) -> None:
        """
        Assert that the ``OrderItem.objects.create()`` method creates the
        expected value.
        """
        # Test object helpers
        price = Decimal('23.34')

        # Create an order item
        order_item: OrderItem = OrderItem.objects.create(
            self.staff,
            item=self.item,
            order=self.order,
            quantity=50,
            unit_price=price
        )

        # Assert that the created order item has the correct details
        self.assertEqual(order_item.created_by, self.staff)
        self.assertEqual(order_item.item, self.item)
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.quantity, 50)
        self.assertEqual(order_item.total_price, price * 50)
        self.assertIsNone(order_item.updated_by)
        self.assertEqual(order_item.unit_price, price)

    def test_creation_by_a_non_admin_non_owning_user_fails(self) -> None:
        """
        Assert that only staff/admin users or the user instance associated with
        the customer of the order object to be associated with the order-item
        to be created can create the order item.
        """
        # Assert that only admin/staff users or the user instance associated
        # with the customer who will own this order-item can create the item.
        with self.assertRaises(ModelValidationError) as cm:
            OrderItem.objects.create(
                self.user2,
                item=self.item,
                order=self.order,
                quantity=50,
                unit_price=self.item.price
            )
        self.assertIn('created_by', cm.exception.message_dict)
        self.assertIn(
            'Only staff users or the customer to be associated with an '
            "order-item's order can add the order-item.",
            cm.exception.message_dict.get('created_by')
        )

    def test_default_unit_price_allocation_during_creation(self) -> None:
        """
        Assert that if the unit price of an order item is not provided during
        creation, then the price of the provided item is used as the unit
        price.
        """
        # Create an order item but don't provide the unit price.
        order_item: OrderItem = OrderItem.objects.create(
            self.user,
            item=self.item,
            order=self.order,
            quantity=50
        )

        # Assert that the unit_price of the created order item is set to the
        # price of the given item.
        self.assertEqual(order_item.unit_price, order_item.item.price)
        self.assertEqual(order_item.total_price, order_item.item.price * 50)

    def test_str(self) -> None:
        """
        Assert that the ``OrderItem.__str__()`` method returns the expected
        value.
        """
        # Dummy test object
        order_item: OrderItem = OrderItemFactory.build(
            item=self.item,
            order=self.order
        )
        order_item.save(self.user)

        # Assert that __str__ returns the expected value
        self.assertEqual(
            str(order_item),
            f'{order_item.order} | {order_item.item}'
        )

    def test_update(self) -> None:
        """
        Assert that the ``OrderItem.update()`` method works as expected.
        """
        # Create order-item object
        order_item: OrderItem = OrderItem.objects.create(
            self.user,
            item=self.item,
            order=self.order
        )
        updated_at = order_item.updated_at

        # Perform an empty update
        order_item.update(self.user)

        # Assert that no modifications were made on the object
        self.assertIsNone(order_item.updated_by)
        self.assertEqual(order_item.updated_at, updated_at)

        # Update the object
        order_item.update(
            self.staff,
            quantity=50,
            unit_price=Decimal('7.00')
        )

        # Assert that the order item was updated correctly
        order_item.refresh_from_db()
        self.assertEqual(order_item.quantity, 50)
        self.assertEqual(order_item.total_price, order_item.unit_price * 50)
        self.assertEqual(order_item.updated_by, self.staff)
        self.assertEqual(order_item.unit_price, Decimal('7.00'))

    def test_unit_price_allocation_by_a_non_admin_user_is_ignored(self) ->\
            None:
        """
        Assert that only staff/admin users can set the unit price of an
        order-item during creation. Allocation of the unit price by non-staff
        users during creation should be ignored silently without raising any
        exceptions and the price of the item should be used instead.
        """
        # Test object helpers.
        price = Decimal('23.34')

        # Create an order item with a custom price and a pass a non-staff user
        # as the creator.
        order_item: OrderItem = OrderItem.objects.create(
            self.user,
            item=self.item,
            order=self.order,
            quantity=50,
            unit_price=price
        )

        # Assert that the given unit_price allocation was ignored and that the
        # price of the given item was used instead.
        self.assertNotEqual(order_item.item.price, price)
        self.assertEqual(order_item.unit_price, order_item.item.price)
        self.assertEqual(order_item.total_price, order_item.item.price * 50)

    def test_unit_price_update_by_a_non_admin_user_is_ignored(self) -> None:
        """
        Assert that only staff/admin users can update the unit price of an
        order-item. Updates of the unit price by non-staff users should be
        ignored silently without raising any exceptions.
        """
        # Create order-item object
        order_item: OrderItem = OrderItem.objects.create(
            self.user,
            item=self.item,
            order=self.order
        )

        # Update the object
        order_item.update(
            self.user,
            quantity=50,
            unit_price=Decimal('7.00')
        )

        # Assert that the order-item's unit price was not updated
        order_item.refresh_from_db()
        self.assertEqual(order_item.unit_price, self.item.price)

        # Assert that the order attributes were updated correctly
        self.assertEqual(order_item.quantity, 50)
        self.assertEqual(order_item.total_price, order_item.unit_price * 50)
        self.assertEqual(order_item.updated_by, self.user)

    def test_update_by_a_non_admin_non_owing_user_fails(self) -> None:
        """
        Assert that only staff/admin users or the user instance associated with
        the customer of the order object associated with an order-item can
        update the order item.
        """
        # Create order-item object
        order_item: OrderItem = OrderItem.objects.create(
            self.user,
            item=self.item,
            order=self.order,
            unit_price=self.item.price
        )

        with self.assertRaises(ModelValidationError) as cm:
            order_item.update(
                self.user2,
                quantity=50,
                unit_price=Decimal('7.00')
            )
        self.assertIn('updated_by', cm.exception.message_dict)
        self.assertIn(
            "Only staff users or the customer associated with an order-item's "
            "order can modify the order-item's details.",
            cm.exception.message_dict.get('updated_by')
        )

        # Assert that the order-item was not updated in the previous attempt
        order_item.refresh_from_db()
        self.assertEqual(order_item.quantity, 1)
        self.assertEqual(order_item.unit_price, self.item.price)
        self.assertIsNone(order_item.updated_by)

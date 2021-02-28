from decimal import Decimal

from django.contrib.auth import get_user_model

from ...core.tests.factories import AdminFactory, UserFactory
from ...core.tests.test_models import AuditBaseTestCase

from ..exceptions import (
    NotEnoughStockError,
    OperationForbiddenError,
    OrderEmptyError,
    OutOfStockError
)
from ..models import Customer, Employee, Inventory, Order, OrderItem

from .factories import (
    CustomerFactory,
    EmployeeFactory,
    InventoryFactory,
    OrderFactory,
    OrderItemFactory
)


# Helpers

User = get_user_model()


# TestCases

class CustomerTests(AuditBaseTestCase):
    """
    Tests for the **Customer** model.
    """

    def test_correct_object_creation(self) -> None:
        """
        Tests for the **Customer.objects.create()** method.
        """
        # Dummy test objects
        staff: User = AdminFactory.create()
        user: User = UserFactory.create()
        user2: User = UserFactory()

        # Create customer object
        customer: Customer = Customer.objects.create(
            user,
            address='An address',
            name='First_name Second_name',
            phone_number='+254722000000',
            user=user
        )

        # Assert that the created customer has the correct details
        self.assertEqual(customer.address, 'An address')
        self.assertEqual(customer.created_by, user)
        self.assertEqual(customer.name, 'First_name Second_name')
        self.assertEqual(customer.phone_number, '+254722000000')
        self.assertIsNone(customer.updated_by)
        self.assertEqual(customer.user, user)

        # Assert that the user property must be provided when creating a
        # customer instance
        with self.assertRaisesMessage(
                ValueError,
                'You must provide the "user" property as a keyword argument'):
            Customer.objects.create(
                user2,
                address='An address',
                name='First_name Second_name',
                phone_number='+254722000000',
                # user=user2  # Missing value
            )

        # Assert that a customer's user property cannot be a staff user
        with self.assertRaisesMessage(
                ValueError,
                'The "user" property must be a non staff user.'):
            CustomerFactory.create(created_by=staff, user=staff)

    def test_make_order(self) -> None:
        """
        Tests for the **Customer.make_order()** method.
        """
        # Dummy Test objects
        user: User = UserFactory.create()
        customer: Customer = CustomerFactory.create(created_by=user)

        # Make order
        order: Order = customer.make_order()

        # Assert that the created order has the correct details
        self.assertIsNotNone(order)
        self.assertEqual(order.created_by, user)
        self.assertEqual(order.customer, customer)
        self.assertTrue(order.is_created)

    def test_str(self) -> None:
        """
        Tests for the **Customer.__str__()** method.
        """
        # Dummy test objects
        customer: Customer = CustomerFactory.create()

        # Assert that __str__ returns the name of the customer
        self.assertEqual(str(customer), customer.name)

    def test_update(self) -> None:
        """
        Tests for the **Customer.update()** method.
        """
        # Dummy test objects
        user: User = UserFactory.create()
        user2: User = UserFactory.create()

        # Create customer object
        customer: Customer = Customer.objects.create(
            user,
            address='An address',
            name='First_name Second_name',
            phone_number='+254722000000',
            user=user
        )

        # Update the object
        customer.update(
            user2,
            address='A different address',
            name='First_name Sur_name',
            phone_number='+254722111111'
        )

        # Assert that the customer instance was updated correctly
        self.assertEqual(customer.address, 'A different address')
        self.assertEqual(customer.created_by, user)
        self.assertEqual(customer.name, 'First_name Sur_name')
        self.assertEqual(customer.phone_number, '+254722111111')
        self.assertEqual(customer.updated_by, user2)
        self.assertEqual(customer.user, user)

    def tearDown(self) -> None:
        # Clear any objects created
        Order.objects.all().delete()
        Customer.objects.all().delete()
        User.objects.all().delete()


class EmployeeTests(AuditBaseTestCase):
    """
    Tests for the **Employee** model.
    """

    def test_correct_object_creation(self) -> None:
        """
        Tests for the **Employee.objects.create()** method.
        """
        # Dummy test objects
        staff: User = AdminFactory.create()
        staff2: User = AdminFactory.create()
        user: User = UserFactory.create()
        user2: User = UserFactory.create()

        # Create employee object
        employee: Employee = Employee.objects.create(
            staff,
            name='First_name Second_name',
            user=staff
        )

        # Assert that the created employee has the correct details
        self.assertEqual(employee.created_by, staff)
        self.assertEqual(employee.name, 'First_name Second_name')
        self.assertEqual(employee.gender, Employee.Gender.get_value('male'))
        self.assertIsNone(employee.updated_by)
        self.assertEqual(employee.user, staff)

        # Assert that the user property must be provided when creating an
        # employee instance
        with self.assertRaisesMessage(
                ValueError,
                'You must provide the "user" property as a keyword argument'):
            Employee.objects.create(
                staff2,
                address='An address',
                name='First_name Second_name',
                # user=staff2  # Missing value
            )

        # Assert that an employee's user property cannot be a non-staff user
        with self.assertRaisesMessage(
                ValueError,
                'The "user" property must be a staff user.'):
            EmployeeFactory.create(created_by=staff2, user=user)

        # Assert that an employee instance cannot be created by a non-staff
        # user
        with self.assertRaisesMessage(
                ValueError,
                'Only staff members can add new employees, "creator" must be '
                'a staff user.'):
            EmployeeFactory.create(created_by=user2)

    def test_str(self) -> None:
        """
        Tests for the **Employee.__str__()** method.
        """
        # Dummy test objects
        employee: Employee = EmployeeFactory.create()

        # Assert that __str__ returns the name of the employee
        self.assertEqual(str(employee), employee.name)

    def test_update(self) -> None:
        """
        Tests for the **Employee.update()** method.
        """
        # Dummy test objects
        user: User = AdminFactory.create()
        user2: User = AdminFactory.create()

        # Create employee object
        employee: Employee = Employee.objects.create(
            user,
            name='First_name Second_name',
            user=user
        )

        # Update the object
        employee.update(
            user2,
            name='First_name Sur_name',
            gender=Employee.Gender.get_value('female')
        )

        # Assert that the employee instance was updated correctly
        self.assertEqual(employee.created_by, user)
        self.assertEqual(employee.name, 'First_name Sur_name')
        self.assertEqual(employee.gender, Employee.Gender.get_value('female'))
        self.assertEqual(employee.updated_by, user2)
        self.assertEqual(employee.user, user)

    def tearDown(self) -> None:
        # Clear any objects created
        Employee.objects.all().delete()
        User.objects.all().delete()


class InventoryTests(AuditBaseTestCase):
    """
    Tests for the **Inventory** model.
    """

    def test_correct_object_creation(self) -> None:
        """
        Tests for the **Inventory.objects.create()** method.
        """
        # Dummy test objects
        staff: User = AdminFactory.create()
        user: User = UserFactory.create()

        # Create an inventory object
        beverage: Inventory = Inventory.objects.create(
            staff,
            beverage_name='Mocha Java',
            on_hand=1000,
            price=Decimal('6.40'),
            warn_limit=100
        )

        # Assert that the created inventory item has the correct state
        self.assertEqual(beverage.beverage_name, 'Mocha Java')
        self.assertEqual(
            beverage.beverage_type,
            Inventory.BeverageTypes.get_value('coffee')
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
            Inventory.InventoryItemState.get_choice_name(
                Inventory.InventoryItemState.get_value('available')
            )
        )
        self.assertIsNone(beverage.updated_by)
        self.assertEqual(beverage.warn_limit, 100)

        # Assert that an inventory item cannot be created by a non-staff user
        with self.assertRaisesMessage(
                ValueError,
                'Only staff members can add new inventory items, "creator" '
                'must be a staff user.'):
            InventoryFactory.create(created_by=user)

    def test_deduct(self) -> None:
        """
        Tests for the **Inventory.deduct()** method.
        """
        # Dummy test objects
        staff: User = AdminFactory.create()

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

        # Perform a deduction
        beverage.deduct(staff, 950)

        # Assert we have the expected state after the deduction
        self.assertFalse(beverage.is_available)
        self.assertTrue(beverage.is_few_remaining)
        self.assertFalse(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 50)
        self.assertEqual(beverage.warn_limit, 100)

        # Assert that attempting to deduct more than the remaining stock will
        # result in a NotEnoughStockError
        with self.assertRaises(NotEnoughStockError):
            beverage.deduct(staff, 100)

        # Assert that no changes to the item were performed with the above
        # deduction attempt
        self.assertFalse(beverage.is_available)
        self.assertTrue(beverage.is_few_remaining)
        self.assertFalse(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 50)
        self.assertEqual(beverage.warn_limit, 100)

        # Perform another deduction
        beverage.deduct(staff, 50)

        # Assert we have the expected state after the deduction
        self.assertFalse(beverage.is_available)
        self.assertTrue(beverage.is_few_remaining)
        self.assertTrue(beverage.is_out_of_stock)
        self.assertEqual(beverage.on_hand, 0)

        # Assert that when a negative quantity is provided, we get an error
        with self.assertRaisesMessage(
                ValueError,
                '"quantity" must be a positive value'):
            beverage.deduct(staff, -10)

    def test_str(self) -> None:
        """
        Tests for the **Inventory.__str__()** method.
        """
        # Dummy test objects
        beverage: Inventory = InventoryFactory.create()

        # Assert that __str__ returns the name of the beverage
        self.assertEqual(str(beverage), beverage.beverage_name)

    def test_update(self) -> None:
        """
        Tests for the **Inventory.update()** method.
        """
        # Dummy test objects
        user: User = AdminFactory.create()
        user2: User = AdminFactory.create()

        # Create an inventory item
        beverage: Inventory = Inventory.objects.create(
            user,
            beverage_name='Mocha Java',
            on_hand=1000,
            price=Decimal('6.40'),
            warn_limit=100
        )

        # Update the item
        beverage.update(
            user2,
            beverage_name='Vanilla Tea',
            beverage_type=Inventory.BeverageTypes.get_value('tea'),
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
            Inventory.BeverageTypes.get_value('tea')
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
            Inventory.InventoryItemState.get_choice_name(
                Inventory.InventoryItemState.get_value('out_of_stock')
            )
        )
        self.assertEqual(beverage.updated_by, user2)
        self.assertEqual(beverage.warn_limit, 10)

    def tearDown(self) -> None:
        # Clear any objects created
        Inventory.objects.all().delete()
        User.objects.all().delete()


class OrderTests(AuditBaseTestCase):
    """
    Tests for the **Order** model.
    """

    def setUp(self) -> None:
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

        # Create order instances
        self.order: Order = OrderFactory.create()
        self.order1: Order = OrderFactory.create(approved=True)
        self.order2: Order = OrderFactory.create(canceled=True)
        self.order3: Order = OrderFactory.create(pending=True)
        self.order4: Order = OrderFactory.create(rejected=True)

    def test_add_item(self) -> None:
        """
        Tests for the **Order.approve()** method.
        """
        # Dummy test objects
        big_price = Decimal('230.15')

        # Get a created order instances
        order: Order = self.order

        # Assert that the order is in the expected state before making any
        # modifications
        self.assertFalse(order.orderitem_set.exists())
        self.assertEqual(order.total_price, Decimal('0.00'))

        # Add an item
        order_item = order.add_item(order.customer.user, self.item1, 100)

        # Assert that the order is in the correct state after the addition
        self.assertTrue(order.orderitem_set.exists())
        self.assertEqual(order.total_price, self.item1.price * 100)

        # Assert that the created item entry is in the correct state
        self.assertEqual(order_item.item, self.item1)
        self.assertEqual(order_item.quantity, 100)
        self.assertEqual(order_item.unit_price, self.item1.price)

        # Add another item
        order_item = order.add_item(
            order.customer.user,
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

        # Assert that adding an out of stock item fails
        with self.assertRaises(OutOfStockError):
            order.add_item(order.customer.user, self.item3)

        # Assert that adding an item to an order that is neither in the
        # "created" or "pending" state fails
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

    def test_approve(self) -> None:
        """
        Tests for the **Order.approve()** method.
        """
        # Dummy test objects
        comments: str = 'Approved'
        employee: Employee = EmployeeFactory.create()

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
        self.assertEqual(order.state, Order.OrderState.get_value('created'))
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
        order.approve(employee, comments)

        # Assert that the order is in the expected state after the approval
        self.assertFalse(order.can_update_order_items)
        self.assertEqual(order.comments, comments)
        self.assertEqual(order.handler, employee)
        self.assertTrue(order.is_approved)
        self.assertFalse(order.is_created)
        self.assertIsNotNone(order.review_date)
        self.assertEqual(order.state, Order.OrderState.get_value('approved'))
        self.assertEqual(
            order.total_price,
            (self.item1.price * 50) + (self.item2.price * 200)
        )
        self.assertEqual(order.updated_by, employee.user)

        # Assert that the stock was adjusted appropriately during approval
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        self.assertTrue(self.item1.is_available)
        self.assertEqual(self.item1.on_hand, 950)
        self.assertFalse(self.item2.is_available)
        self.assertTrue(self.item2.is_few_remaining)
        self.assertEqual(self.item2.on_hand, 50)

        # Get a pending order instances
        order1: Order = self.order3

        # The order shouldn't have any items
        self.assertFalse(order1.orderitem_set.exists())

        # Assert that approving an order with an empty item list fails
        self.assertRaises(OrderEmptyError, order1.approve, employee)

        # Add an item to the order
        order1.add_item(order1.customer.user, self.item2, 100)

        # Assert that approving an order of more than available stock fails
        self.assertRaises(NotEnoughStockError, order1.approve, employee)

        # Assert that attempting to approve an order that is not in the
        # "pending" fails
        self.assertRaises(
            OperationForbiddenError,
            self.order1.approve,
            employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order2.approve,
            employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order.approve,
            employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order4.approve,
            employee,
            comments
        )

    def test_cancel(self) -> None:
        """
        Tests for the **Order.cancel()** method.
        """
        # Get a created order instances
        order: Order = self.order

        # Assert that the order is in the expected state before making any
        # modifications
        self.assertTrue(order.can_update_order_items)
        self.assertIsNone(order.comments)
        self.assertFalse(order.is_canceled)
        self.assertTrue(order.is_created)
        self.assertEqual(order.state, Order.OrderState.get_value('created'))

        # Cancel the order
        order.cancel(order.customer.user, 'Changed my mind')

        # Assert that the order is in the expected state after the
        # cancellation
        self.assertFalse(order.can_update_order_items)
        self.assertEqual(order.comments, 'Changed my mind')
        self.assertTrue(order.is_canceled)
        self.assertFalse(order.is_created)
        self.assertEqual(order.state, Order.OrderState.get_value('canceled'))
        self.assertEqual(order.updated_by, order.customer.user)

        # Cancellation of a pending order should not fail
        self.assertTrue(self.order3.is_pending)

        self.order3.cancel(self.order3.customer.user)

        self.assertIsNone(self.order3.comments)
        self.assertTrue(self.order3.is_canceled)
        self.assertEqual(self.order3.updated_by, self.order3.customer.user)

        # Assert that cancellation of orders not in the "created" or "pending"
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
        Tests for the **Order.objects.create()** method.
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
        self.assertEqual(order.state, Order.OrderState.get_value('created'))
        self.assertEqual(order.total_price, Decimal('0.00'))

    def test_get_item(self) -> None:
        """
        Tests for the **Order.get_item()** method.
        """
        ...

    def test_has_item(self) -> None:
        """
        Tests for the **Order.has_item()** method.
        """
        ...

    def test_mark_ready_for_review(self) -> None:
        """
        Tests for the **Order.mark_ready_for_review()** method.
        """
        # Get a created order instances
        order: Order = self.order

        # Assert that the order is in the expected state before making any
        # modifications
        self.assertTrue(order.can_update_order_items)
        self.assertTrue(order.is_created)
        self.assertFalse(order.is_pending)
        self.assertEqual(order.state, Order.OrderState.get_value('created'))
        self.assertEqual(order.total_price, Decimal('0.00'))

        # Assert that attempting to mark an order with an empty item list as
        # "pending" fails
        self.assertRaises(
            OrderEmptyError,
            order.mark_ready_for_review,
            order.customer.user
        )

        # Add an item to the order
        order.add_item(order.customer.user, self.item1, 50)

        # Mark the order as "pending" and assert that the order is in the
        # expected state
        order.mark_ready_for_review(order.customer.user)
        self.assertTrue(order.can_update_order_items)
        self.assertFalse(order.is_created)
        self.assertTrue(order.is_pending)
        self.assertEqual(order.state, Order.OrderState.get_value('pending'))
        self.assertEqual(order.total_price, self.item1.price * 50)
        self.assertEqual(order.updated_by, order.customer.user)

        # Assert that attempting to mark an order that is not in the "created"
        # state as "pending" fails
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
        Tests for the **Order.reject()** method.
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
        self.assertEqual(order.state, Order.OrderState.get_value('pending'))

        # Reject the order
        order.reject(employee, comments)

        # Assert that the order is in the expected state after the rejection
        self.assertFalse(order.can_update_order_items)
        self.assertEqual(order.comments, comments)
        self.assertEqual(order.handler, employee)
        self.assertFalse(order.is_pending)
        self.assertTrue(order.is_rejected)
        self.assertIsNotNone(order.review_date)
        self.assertEqual(order.state, Order.OrderState.get_value('rejected'))
        self.assertEqual(order.updated_by, employee.user)

        # Assert that attempting to reject an order that is not in the
        # "pending" fails
        self.assertRaises(
            OperationForbiddenError,
            self.order1.reject,
            employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order2.reject,
            employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order.reject,
            employee,
            comments
        )
        self.assertRaises(
            OperationForbiddenError,
            self.order4.reject,
            employee,
            comments
        )

    def test_remove_item(self) -> None:
        """
        Tests for the **Order.remove_item()** method.
        """
        ...

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
        Tests for the **Order.update()** method.
        """
        # Skip for now. The model's mutators should be used to perform any
        # updates on the model's instances
        ...

    def test_update_item(self) -> None:
        """
        Tests for the **Order.update_item()** method.
        """
        ...

    def tearDown(self) -> None:
        # Clear any objects created
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Customer.objects.all().delete()
        Inventory.objects.all().delete()
        Employee.objects.all().delete()
        User.objects.all().delete()


class OrderItemTests(AuditBaseTestCase):
    """
    Tests for the **OrderItem** model.
    """

    def test_correct_object_creation(self) -> None:
        """
        Tests for the **OrderItem.objects.create()** method.
        """
        # Dummy test objects
        item: Inventory = InventoryFactory.create()
        order: Order = OrderFactory.create()
        user: User = UserFactory.create()

        # Create an order item
        order_item: OrderItem = OrderItem.objects.create(
            user,
            item=item,
            order=order,
            quantity=50,
            unit_price=item.price
        )

        # Assert that the created order item has the correct details
        self.assertEqual(order_item.created_by, user)
        self.assertEqual(order_item.item, item)
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.quantity, 50)
        self.assertEqual(order_item.total_price, order_item.unit_price * 50)
        self.assertIsNone(order_item.updated_by)
        self.assertEqual(order_item.unit_price, item.price)

    def test_str(self) -> None:
        """
        Tests for the **Employee.__str__()** method.
        """
        # Dummy test objects
        user: User = UserFactory.create()
        order_item: OrderItem = OrderItemFactory.build(
            item=InventoryFactory.create(),
            order=OrderFactory.create()
        )
        order_item.save(user)

        # Assert that __str__ returns the expected value
        self.assertEqual(
            str(order_item),
            f'{order_item.order} | {order_item.item}'
        )

    def test_update(self) -> None:
        """
        Tests for the **Employee.update()** method.
        """
        # Dummy test objects
        user: User = UserFactory.create()
        user2: User = AdminFactory.create()

        # Create employee object
        order_item: OrderItem = OrderItem.objects.create(
            user,
            item=InventoryFactory.create(),
            order=OrderFactory.create()
        )
        updated_at = order_item.updated_at

        # Perform an empty update
        order_item.update(user)

        # Assert that modifications were made on the object
        self.assertIsNone(order_item.updated_by)
        self.assertEqual(order_item.updated_at, updated_at)

        # Update the object
        order_item.update(
            user2,
            quantity=50,
            unit_price=Decimal('7.00')
        )

        # Assert that the order item was updated correctly
        self.assertEqual(order_item.quantity, 50)
        self.assertEqual(order_item.total_price, order_item.unit_price * 50)
        self.assertEqual(order_item.updated_by, user2)
        self.assertEqual(order_item.unit_price, Decimal('7.00'))

    def tearDown(self) -> None:
        # Clear any objects created
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Customer.objects.all().delete()
        Inventory.objects.all().delete()
        Employee.objects.all().delete()
        User.objects.all().delete()

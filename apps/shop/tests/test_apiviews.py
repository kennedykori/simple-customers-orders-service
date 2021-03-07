from decimal import Decimal
from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import (
    APIRequestFactory,
    APITestCase,
    force_authenticate
)

from ...core.tests.factories import AdminFactory, UserFactory

from ..models import Customer, Employee, Inventory, Order
from ..serializers import (
    InventorySerializer,
    LimitedInventorySerializer,
    OrderSerializer
)
from ..apiviews import InventoryViewSet

from .factories import (
    CustomerFactory,
    EmployeeFactory,
    InventoryFactory,
    OrderFactory,
    OrderItemFactory
)


# Constant

User = get_user_model()


# TestCases

# noinspection PyUnresolvedReferences
class CustomerViewSetTests(APITestCase):
    """
    Tests for the **CustomerViewSet** class.
    """

    def test_create_customer(self) -> None:
        """
        Ensure that the **CustomerViewSet.create** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        user: User = UserFactory.create()
        user1: User = UserFactory.create()

        url: str = reverse('customers-list')
        data = {
            'name': 'First_Name Second_Name',
            'address': 'An address',
            'phone_number': '+254722000000',
            'user': user.pk
        }

        # Assert that creating an object works as expected
        self.client.force_authenticate(user=user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert that admin can create customer instances
        data['user'] = user1.pk
        self.client.force_authenticate(user=admin)
        response = self.client.post(url, data, format='json')

        self.assertEqual(Customer.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert the user instance associated with an object cannot be an
        # admin
        data['user'] = admin.pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(Customer.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user', response.data.keys())

    def test_make_order(self) -> None:
        """
        Ensure that the **CustomerViewSet.make_order** action works as
        expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer1: Customer = CustomerFactory.create()

        url: str = reverse('customers-make-order', args=[customer.pk])
        data = {
            'customer': customer.pk
        }

        # Assert that a customer can create a new order
        self.client.force_authenticate(user=customer.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        # Assert that a customer cannot create an order for another user
        self.client.force_authenticate(user=customer1.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Order.objects.count(), 1)

        # Assert that a staff user can create orders for customers
        self.client.force_authenticate(user=admin)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)

        data['customer'] = customer1.pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 3)

        # Assert that invalid data fails
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 3)

    def test_list_customers(self) -> None:
        """
        Ensure that the **CustomerViewSet.list** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        CustomerFactory.create()

        url: str = reverse('customers-list')

        # Assert that when a customer is logged on, he/she cannot see other
        # customer's details
        self.client.force_authenticate(user=customer.user)
        response = self.client.get(url, {}, format='json')

        self.assertEqual(len(response.data.get('customers')), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that when an employee is logged on, he/she can see all the
        # customers' details
        self.client.force_authenticate(user=admin)
        response = self.client.get(url, {}, format='json')

        self.assertEqual(len(response.data.get('customers')), 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_customer(self) -> None:
        """
        Ensure that the **CustomerViewSet.update** action works as expected.
        """
        # Test data
        customer: Customer = CustomerFactory.create()
        user: User = UserFactory.create()

        url: str = reverse('customers-detail', args=[customer.pk])
        data = {
            'name': 'First_Name Second_Name',
            'address': 'A new address',
            'phone_number': '+254722222222',
            'user': user.pk
        }

        # Assert that a customer cannot change the user object associated
        # his/her account
        self.client.force_authenticate(user=customer.user)
        response = self.client.put(url, data, format='json')

        self.assertIn('user', response.data.keys())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that with the correct data ,update works as expected
        data['user'] = customer.user.pk
        response = self.client.put(url, data, format='json')
        customer.refresh_from_db()

        self.assertEqual(customer.address, data['address'])
        self.assertEqual(customer.name, data['name'])
        self.assertEqual(customer.phone_number, data['phone_number'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# noinspection PyUnresolvedReferences
class EmployeeViewSetTests(APITestCase):
    """
    Tests for the **EmployeeViewSet** class.
    """

    def test_create_employee(self) -> None:
        """
        Ensure that the **EmployeeViewSet.create** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        user: User = UserFactory.create()

        url: str = reverse('employees-list')
        data = {
            'name': 'First_Name Second_Name',
            'gender': 'F',
            'user': admin.pk
        }

        # Assert that creating an object works as expected
        self.client.force_authenticate(user=admin)
        response = self.client.post(url, data, format='json')

        self.assertEqual(Employee.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert the user instance associated with an object must be an
        # admin
        data['user'] = user.pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(Employee.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_customer(self) -> None:
        """
        Ensure that the **EmployeeViewSet.update** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        employee: Employee = EmployeeFactory.create()

        url: str = reverse('employees-detail', args=[employee.pk])
        data = {
            'name': 'First_Name Second_Name',
            'gender': 'F',
            'user': admin.pk
        }

        # Assert that an employee cannot change the user object associated
        # his/her account
        self.client.force_authenticate(user=employee.user)
        response = self.client.put(url, data, format='json')

        self.assertIn('user', response.data.keys())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that with the correct data ,update works as expected
        data['user'] = employee.user.pk
        response = self.client.put(url, data, format='json')
        employee.refresh_from_db()

        self.assertEqual(employee.gender, data['gender'])
        self.assertEqual(employee.name, data['name'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# noinspection PyTypeChecker,PyUnresolvedReferences
class InventoryViewSetTests(APITestCase):
    """
    Tests for the **InventoryViewSet** class.
    """

    def test_list_inventories(self) -> None:
        """
        Ensure that the **InventoryViewSet.list** action works as expected.
        """
        # Test data
        stock: List[Inventory] = InventoryFactory.create_batch(5)
        admin: User = AdminFactory.create()

        # Request data
        factory = APIRequestFactory()
        url: str = reverse('inventories-list')
        view = InventoryViewSet.as_view({'get': 'list'})

        # Assert that admins get the expected data
        request = factory.get(url)
        force_authenticate(request, user=admin)
        response = view(request)

        self.assertListEqual(
            response.data['inventories'],
            InventorySerializer(
                stock,
                many=True,
                context={'request': request}
            ).data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that non authenticated requests return the expected data
        request = factory.get(url)
        response = view(request)

        self.assertListEqual(
            response.data['inventories'],
            LimitedInventorySerializer(
                stock,
                many=True,
                context={'request': request}
            ).data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_inventory(self) -> None:
        """
        Ensure that the **InventoryViewSet.update** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        inventory: Inventory = InventoryFactory.create()
        user: User = UserFactory.create()

        # Request data
        url: str = reverse('inventories-detail', args=[inventory.pk])
        data = {'beverage_name': 'Mocha Java'}

        # Assert that non staff user's can neither access nor update an
        # inventory item
        self.client.force_authenticate(user=user)
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Assert that a staff user can access and update an inventory item
        self.client.force_authenticate(user=admin)
        response = self.client.put(url, data, format='json')

        inventory.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(inventory.beverage_name, data['beverage_name'])


# noinspection PyUnresolvedReferences
class OrderViewSetTests(APITestCase):
    """
    Tests for the **OrderViewSet** class.
    """

    def test_add_item(self) -> None:
        """
        Ensure that the **OrderViewSet.add_item** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer2: Customer = CustomerFactory.create()
        inventories: List[Inventory] = InventoryFactory.create_batch(
            3,
            on_hand=1000,
            price=Decimal(10.00)
        )
        order = OrderFactory.create(customer=customer)
        order1 = OrderFactory.create(customer=customer, approved=True)
        order2 = OrderFactory.create(customer=customer, canceled=True)
        order3 = OrderFactory.create(customer=customer, pending=True)
        order4 = OrderFactory.create(customer=customer, rejected=True)

        # Request data
        data = {
            'item': inventories[0].pk,
            'quantity': 5,
            'unit_price': '100.00'
        }
        url: str = reverse('orders-add-item', args=[order.pk])

        # Assert that trying to add an invalid item fails
        self.client.force_authenticate(user=customer.user)
        response = self.client.post(url, {}, format='json')

        self.assertEqual(order.orderitem_set.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that with the correct data, add works as expected
        response = self.client.post(url, data, format='json')

        self.assertEqual(order.orderitem_set.count(), 1)
        self.assertEqual(response.data['quantity'], 5)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Assert that non-staff users cannot modify item prices
        self.assertNotEqual(response.data['unit_price'], '100.00')

        # Assert that multiple items can be added to an order
        data['item'] = inventories[1].pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(order.orderitem_set.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert that a customer cannot alter the item list of another
        # customer's order
        self.client.force_authenticate(user=customer2.user)
        data['item'] = inventories[2].pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(order.orderitem_set.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Assert that staff members can alter the item list of any customer's
        # order
        self.client.force_authenticate(user=admin)
        response = self.client.post(url, data, format='json')

        self.assertEqual(order.orderitem_set.count(), 3)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Assert that staff users can modify item prices
        self.assertEqual(response.data['unit_price'], '100.00')

        # Assert that adding an item that is already on an order's item list
        # fails
        response = self.client.post(url, data, format='json')

        self.assertEqual(order.orderitem_set.count(), 3)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.data,
            {
                'item': ['This item already exists in this order.']
            }
        )

        # Assert that adding items to pending orders is allowed
        url: str = reverse('orders-add-item', args=[order3.pk])
        response = self.client.post(url, data, format='json')

        self.assertEqual(order3.orderitem_set.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert that adding items to non created nor pending orders fail
        # APPROVED ORDERS
        url: str = reverse('orders-add-item', args=[order1.pk])
        response = self.client.post(url, data, format='json')

        self.assertEqual(order1.orderitem_set.count(), 0)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # Assert that adding items to non created nor pending orders fail
        # CANCELED ORDERS
        url: str = reverse('orders-add-item', args=[order2.pk])
        response = self.client.post(url, data, format='json')

        self.assertEqual(order2.orderitem_set.count(), 0)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # Assert that adding items to non created nor pending orders fail
        # REJECTED ORDERS
        url: str = reverse('orders-add-item', args=[order4.pk])
        response = self.client.post(url, data, format='json')

        self.assertEqual(order4.orderitem_set.count(), 0)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_approve(self) -> None:
        """
        Ensure that the **OrderViewSet.approve** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer2: Customer = CustomerFactory.create()
        employee: Employee = EmployeeFactory.create()
        inventories: List[Inventory] = InventoryFactory.create_batch(
            2,
            on_hand=1000
        )
        order: Order = OrderFactory.create(customer=customer, pending=True)
        order1: Order = OrderFactory.create(customer=customer)
        order2: Order = OrderFactory.create(customer=customer2)
        order3: Order = OrderFactory.create(customer=customer2, pending=True)
        order4: Order = OrderFactory.create(customer=customer2, pending=True)

        # Add items to orders
        order2.add_item(customer2.user, inventories[0], 10)
        order3.add_item(customer2.user, inventories[0], 20)
        order4.add_item(customer2.user, inventories[0], 20)

        # Test Data
        data = {
            'comments': f'You were served by {employee.name}.',
            'handler': employee.pk
        }
        url = reverse('orders-approve', args=[order.pk])

        # Assert that customers cannot approve orders, only employees are
        # allowed to approve orders
        self.client.force_authenticate(user=customer.user)
        response = self.client.patch(url, data, format='json')

        order.refresh_from_db(fields=['state'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(order.state, Order.OrderState.PENDING.choice_value)

        # Assert that a blank order cannot be approved
        self.assertEquals(order.orderitem_set.count(), 0)

        self.client.force_authenticate(user=admin)
        response = self.client.patch(url, data, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_424_FAILED_DEPENDENCY
        )

        # Assert that approving an order with items exceeding the available
        # stock fails
        order.add_item(customer.user, inventories[0])
        order.add_item(customer.user, inventories[1], 1500)
        response = self.client.patch(url, data, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        self.assertDictEqual(
            response.data,
            {
                'adjustment': 1500,
                'available_stock': 1000,
                'detail': (
                    'The current stock, "1000" of item, "%s" is not enough '
                    'for a deduction by "1500" units.' % inventories[1]
                ),
                'item': inventories[1].pk
            }
        )

        # Assert that a blank comment isn't allowed
        response = self.client.patch(
            url,
            {'comments': '', 'handler': employee.pk},
            format='json'
        )

        order.refresh_from_db(fields=['state'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(order.state, Order.OrderState.PENDING.choice_value)

        # Assert that the action works as expected when performed by an
        # employee and when given valid data
        order.update_item(customer.user, inventories[1], 3)
        self.client.force_authenticate(user=employee.user)
        response = self.client.patch(url, data, format='json')

        order.refresh_from_db(
            fields=['comments', 'handler', 'review_date', 'state']
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(order.comments, data['comments'])
        self.assertEqual(order.handler, employee)
        self.assertIsNotNone(order.review_date)
        self.assertEqual(order.state, Order.OrderState.APPROVED.choice_value)

        # Assert that orders that are not in the PENDING state cannot be
        # approved
        # CREATED ORDER
        url = reverse('orders-approve', args=[order1.pk])
        response = self.client.patch(url, data, format='json')

        order1.refresh_from_db(fields=['state'])
        self.assertEqual(order1.state, Order.OrderState.CREATED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # APPROVED ORDER
        order4.approve(employee)
        url = reverse('orders-approve', args=[order4.pk])
        response = self.client.patch(url, data, format='json')

        order4.refresh_from_db(fields=['state'])
        self.assertEqual(order4.state, Order.OrderState.APPROVED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # REJECTED ORDER
        order3.reject(employee, 'A good reason')
        url = reverse('orders-approve', args=[order3.pk])
        response = self.client.patch(url, data, format='json')

        order3.refresh_from_db(fields=['state'])
        self.assertEqual(order3.state, Order.OrderState.REJECTED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # CANCELED ORDER
        order2.cancel(customer2.user, 'A good reason')
        url = reverse('orders-approve', args=[order2.pk])
        response = self.client.patch(url, data, format='json')

        order2.refresh_from_db(fields=['state'])
        self.assertEqual(order2.state, Order.OrderState.CANCELED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_cancel(self) -> None:
        """
        Ensure that the **OrderViewSet.cancel** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer2: Customer = CustomerFactory.create()
        employee: Employee = EmployeeFactory.create()
        inventories: List[Inventory] = InventoryFactory.create_batch(
            2,
            on_hand=1000
        )
        order: Order = OrderFactory.create(customer=customer)
        order1: Order = OrderFactory.create(customer=customer, pending=True)
        order2: Order = OrderFactory.create(customer=customer2)
        order3: Order = OrderFactory.create(customer=customer2, pending=True)
        order4: Order = OrderFactory.create(customer=customer2, pending=True)

        # Add items to orders
        order.add_item(customer.user, inventories[0])
        order.add_item(customer.user, inventories[1], 3)
        order2.add_item(customer2.user, inventories[0], 10)
        order3.add_item(customer2.user, inventories[0], 20)
        order4.add_item(customer2.user, inventories[0], 20)

        # Test Data
        data = {'comments': 'A good reason'}
        url = reverse('orders-cancel', args=[order.pk])

        # Assert that the action fails when a blank comment is given
        self.client.force_authenticate(user=customer.user)
        response = self.client.patch(url, {'comments': ''}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(order.state, Order.OrderState.CREATED.choice_value)

        # Assert that the action works as expected when given valid data
        response = self.client.patch(url, data, format='json')

        order.refresh_from_db(fields=['comments', 'state'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(order.comments, data['comments'])
        self.assertEqual(order.state, Order.OrderState.CANCELED.choice_value)

        # Assert that a pending order can be canceled
        url = reverse('orders-cancel', args=[order1.pk])
        response = self.client.patch(url, format='json')

        order1.refresh_from_db(fields=['comments', 'state'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(order1.state, Order.OrderState.CANCELED.choice_value)
        self.assertIsNone(order1.comments)

        # Assert that a customer cannot change the state of another customer's
        # order
        url = reverse('orders-cancel', args=[order2.pk])
        response = self.client.patch(url, data, format='json')

        order2.refresh_from_db(fields=['state'])
        self.assertEqual(order2.state, Order.OrderState.CREATED.choice_value)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Assert that an admin can change the state of any customer's order
        self.client.force_authenticate(user=admin)
        response = self.client.patch(url, data, format='json')

        order2.refresh_from_db(fields=['comments', 'state'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(order2.comments, data['comments'])
        self.assertEqual(order2.state, Order.OrderState.CANCELED.choice_value)

        # Assert that orders that are not in the created or pending state
        # cannot be CANCELED
        # CANCELED ORDER
        response = self.client.patch(url, data, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # APPROVED ORDER
        order3.approve(employee)
        url = reverse('orders-cancel', args=[order3.pk])
        response = self.client.patch(url, data, format='json')

        order3.refresh_from_db(fields=['state'])
        self.assertEqual(order3.state, Order.OrderState.APPROVED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # REJECTED ORDER
        order4.reject(employee, 'A good reason')
        url = reverse('orders-cancel', args=[order4.pk])
        response = self.client.patch(url, data, format='json')

        order4.refresh_from_db(fields=['state'])
        self.assertEqual(order4.state, Order.OrderState.REJECTED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_list_orders(self) -> None:
        """
        Ensure that the **OrderViewSet.list** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer2: Customer = CustomerFactory.create()
        OrderFactory.create_batch(3, customer=customer)
        OrderFactory.create_batch(5, customer=customer2)

        # Request data
        url: str = reverse('orders-list')

        # Assert that when a customer is logged on, he/she cannot see other
        # customer's orders
        self.client.force_authenticate(user=customer.user)
        response = self.client.get(url, format='json')

        self.assertEqual(len(response.data.get('orders')), 3)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=customer2.user)
        response = self.client.get(url, format='json')

        self.assertEqual(len(response.data.get('orders')), 5)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that when an employee is logged on, he/she can see all the
        # customers' orders
        self.client.force_authenticate(user=admin)
        response = self.client.get(url, format='json')

        self.assertEqual(len(response.data.get('orders')), 8)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_for_review(self) -> None:
        """
        Ensure that the **OrderViewSet.mark_ready_for_review** action works as
        expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer2: Customer = CustomerFactory.create()
        employee: Employee = EmployeeFactory.create()
        inventories: List[Inventory] = InventoryFactory.create_batch(
            2,
            on_hand=1000
        )
        order: Order = OrderFactory.create(customer=customer)
        order1: Order = OrderFactory.create(customer=customer)
        order2: Order = OrderFactory.create(customer=customer2)
        order3: Order = OrderFactory.create(customer=customer2, pending=True)
        order4: Order = OrderFactory.create(customer=customer2, pending=True)

        # Add items to orders
        order.add_item(customer.user, inventories[0])
        order.add_item(customer.user, inventories[1], 3)
        order2.add_item(customer2.user, inventories[0], 10)
        order3.add_item(customer2.user, inventories[0], 20)
        order4.add_item(customer2.user, inventories[0], 20)

        # Test Data
        url = reverse('orders-mark-ready-for-review', args=[order.pk])

        # Assert that the action works as expected
        self.client.force_authenticate(user=customer.user)
        response = self.client.patch(url, format='json')

        order.refresh_from_db(fields=['state'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(order.state, Order.OrderState.PENDING.choice_value)

        # Assert that the an empty order cannot be marked as ready
        url = reverse('orders-mark-ready-for-review', args=[order1.pk])
        response = self.client.patch(url, format='json')

        order1.refresh_from_db(fields=['state'])
        self.assertEqual(order1.state, Order.OrderState.CREATED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_424_FAILED_DEPENDENCY
        )

        # Assert that a customer cannot change the state of another customer's
        # order
        url = reverse('orders-mark-ready-for-review', args=[order2.pk])
        response = self.client.patch(url, format='json')

        order2.refresh_from_db(fields=['state'])
        self.assertEqual(order2.state, Order.OrderState.CREATED.choice_value)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Assert that an admin can change the state of any customer's order
        self.client.force_authenticate(user=admin)
        response = self.client.patch(url, format='json')

        order2.refresh_from_db(fields=['state'])
        self.assertEqual(order2.state, Order.OrderState.PENDING.choice_value)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that orders that are not in the created state cannot be
        # marked as pending
        # PENDING ORDER
        url = reverse('orders-mark-ready-for-review', args=[order2.pk])
        response = self.client.patch(url, format='json')

        order2.refresh_from_db(fields=['state'])
        self.assertEqual(order2.state, Order.OrderState.PENDING.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # APPROVED ORDER
        order2.approve(employee)
        response = self.client.patch(url, format='json')

        order2.refresh_from_db(fields=['state'])
        self.assertEqual(order2.state, Order.OrderState.APPROVED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # REJECTED ORDER
        order3.reject(employee, 'A good reason')
        url = reverse('orders-mark-ready-for-review', args=[order3.pk])
        response = self.client.patch(url, format='json')

        order3.refresh_from_db(fields=['state'])
        self.assertEqual(order3.state, Order.OrderState.REJECTED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # CANCELED ORDER
        order4.cancel(customer2.user, 'A good reason')
        url = reverse('orders-mark-ready-for-review', args=[order4.pk])
        response = self.client.patch(url, format='json')

        order4.refresh_from_db(fields=['state'])
        self.assertEqual(order4.state, Order.OrderState.CANCELED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_reject(self) -> None:
        """
        Ensure that the **OrderViewSet.reject** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer2: Customer = CustomerFactory.create()
        employee: Employee = EmployeeFactory.create()
        inventories: List[Inventory] = InventoryFactory.create_batch(
            2,
            on_hand=1000
        )
        order: Order = OrderFactory.create(customer=customer, pending=True)
        order1: Order = OrderFactory.create(customer=customer)
        order2: Order = OrderFactory.create(customer=customer2)
        order3: Order = OrderFactory.create(customer=customer2, pending=True)
        order4: Order = OrderFactory.create(customer=customer2, pending=True)

        # Add items to orders
        order.add_item(customer.user, inventories[0])
        order.add_item(customer.user, inventories[1], 3)
        order2.add_item(customer2.user, inventories[0], 10)
        order3.add_item(customer2.user, inventories[0], 20)
        order4.add_item(customer2.user, inventories[0], 20)

        # Test Data
        data = {
            'comments': 'A good reason',
            'handler': employee.pk
        }
        url = reverse('orders-reject', args=[order.pk])

        # Assert that customers cannot reject orders, only employees should be
        # able to reject orders
        self.client.force_authenticate(user=customer.user)
        response = self.client.patch(url, data, format='json')

        order.refresh_from_db(fields=['state'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(order.state, Order.OrderState.PENDING.choice_value)

        # Assert that a reason for the rejection has to be provided
        self.client.force_authenticate(user=admin)
        response = self.client.patch(
            url,
            {'handler': employee.pk},
            format='json'
        )

        order.refresh_from_db(fields=['state'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(order.state, Order.OrderState.PENDING.choice_value)

        # Assert that the action works as expected when performed by an
        # employee
        self.client.force_authenticate(user=employee.user)
        response = self.client.patch(url, data, format='json')

        order.refresh_from_db(
            fields=['comments', 'handler', 'review_date', 'state']
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(order.comments, data['comments'])
        self.assertEqual(order.handler, employee)
        self.assertIsNotNone(order.review_date)
        self.assertEqual(order.state, Order.OrderState.REJECTED.choice_value)

        # Assert that orders that are not in the pending state cannot be
        # rejected
        # CREATED ORDER
        url = reverse('orders-reject', args=[order1.pk])
        response = self.client.patch(url, data, format='json')

        order1.refresh_from_db(fields=['state'])
        self.assertEqual(order1.state, Order.OrderState.CREATED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # APPROVED ORDER
        order4.approve(employee)
        url = reverse('orders-reject', args=[order4.pk])
        response = self.client.patch(url, data, format='json')

        order4.refresh_from_db(fields=['state'])
        self.assertEqual(order4.state, Order.OrderState.APPROVED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # REJECTED ORDER
        order3.reject(employee, 'A good reason')
        url = reverse('orders-reject', args=[order3.pk])
        response = self.client.patch(url, data, format='json')

        order3.refresh_from_db(fields=['state'])
        self.assertEqual(order3.state, Order.OrderState.REJECTED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # CANCELED ORDER
        order2.cancel(customer2.user, 'A good reason')
        url = reverse('orders-reject', args=[order2.pk])
        response = self.client.patch(url, data, format='json')

        order2.refresh_from_db(fields=['state'])
        self.assertEqual(order2.state, Order.OrderState.CANCELED.choice_value)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_remove_item(self) -> None:
        """
        Ensure that the **OrderViewSet.remove_item** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer2: Customer = CustomerFactory.create()
        employee: Employee = EmployeeFactory.create()
        inventories: List[Inventory] = InventoryFactory.create_batch(
            4,
            on_hand=1000,
            price=Decimal(10.00)
        )
        order: Order = OrderFactory.create(customer=customer)
        order1: Order = OrderFactory.create(customer=customer, pending=True)
        order2: Order = OrderFactory.create(customer=customer2)
        order3: Order = OrderFactory.create(customer=customer2, pending=True)

        # Add items to orders
        order.add_item(customer.user, inventories[0])
        order.add_item(customer.user, inventories[1], 3)
        order.add_item(customer.user, inventories[2], 20)
        order1.add_item(customer.user, inventories[0])
        order1.add_item(customer.user, inventories[1], 5)
        order2.add_item(customer2.user, inventories[0], 10)
        order3.add_item(customer2.user, inventories[0], 20)

        # Request data
        data = {'item': inventories[0].pk}
        url: str = reverse('orders-remove-item', args=[order.pk])

        # Assert that trying to remove an item with invalid details fails
        self.client.force_authenticate(user=customer.user)
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that with the correct data, remove item works as expected
        self.assertEqual(order.orderitem_set.count(), 3)
        response = self.client.post(url, data, format='json')

        self.assertEqual(order.orderitem_set.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Assert that any item of an order can be removed
        data['item'] = inventories[1].pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(order.orderitem_set.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Assert that a customer cannot alter the item list of another
        # customer's order
        self.client.force_authenticate(user=customer2.user)
        data['item'] = inventories[2].pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Assert that staff members can alter the item list of any customer's
        # order
        self.client.force_authenticate(user=admin)
        response = self.client.post(url, data, format='json')

        self.assertEqual(order.orderitem_set.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Assert that removing an item that is not in an order's item list
        # fails
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.data,
            {
                'item': ["This item doesn't exists in this order."]
            }
        )

        # Assert that removing items on a pending orders is allowed
        url: str = reverse('orders-remove-item', args=[order1.pk])
        data['item'] = inventories[1].pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(order1.orderitem_set.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Assert that removing items to a non created nor pending orders fails
        data['item'] = inventories[0].pk
        order1.approve(employee)  # APPROVED ORDER
        response = self.client.post(url, data, format='json')

        self.assertEqual(order1.orderitem_set.count(), 1)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # Assert that removing items to a non created nor pending orders fails
        order2.cancel(customer2.user)  # CANCELED ORDER
        url: str = reverse('orders-remove-item', args=[order2.pk])
        response = self.client.post(url, data, format='json')

        self.assertEqual(order2.orderitem_set.count(), 1)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # Assert that removing items to a non created nor pending orders fails
        order3.reject(employee, 'A good reason')  # REJECTED ORDER
        url: str = reverse('orders-remove-item', args=[order3.pk])
        response = self.client.post(url, data, format='json')

        self.assertEqual(order3.orderitem_set.count(), 1)
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_update_item(self) -> None:
        """
        Ensure that the **OrderViewSet.update_item** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer2: Customer = CustomerFactory.create()
        employee: Employee = EmployeeFactory.create()
        inventories: List[Inventory] = InventoryFactory.create_batch(
            4,
            on_hand=1000,
            price=Decimal(10.00)
        )
        order: Order = OrderFactory.create(customer=customer)
        order1: Order = OrderFactory.create(customer=customer, pending=True)
        order2: Order = OrderFactory.create(customer=customer2)
        order3: Order = OrderFactory.create(customer=customer2, pending=True)

        # Add items to orders
        order.add_item(customer.user, inventories[0])
        order.add_item(customer.user, inventories[1], 3)
        order.add_item(customer.user, inventories[2], 20)
        order1.add_item(customer.user, inventories[0])
        order2.add_item(customer2.user, inventories[0], 10)
        order3.add_item(customer2.user, inventories[0], 20)

        # Request data
        data = {
            'item': inventories[0].pk,
            'quantity': 5,
            'unit_price': '100.00'
        }
        url: str = reverse('orders-update-item', args=[order.pk])

        # Assert that trying to update an item with invalid details fails
        self.client.force_authenticate(user=customer.user)
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that with the correct data, update item works as expected
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.data['quantity'], 5)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert that non-staff users cannot modify item prices
        self.assertNotEqual(response.data['unit_price'], '100.00')

        # Assert that any item of an order can be updated
        data['item'] = inventories[1].pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.data['quantity'], 5)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that a customer cannot alter the item list of another
        # customer's order
        self.client.force_authenticate(user=customer2.user)
        data['item'] = inventories[2].pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Assert that staff members can alter the item list of any customer's
        # order
        self.client.force_authenticate(user=admin)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.data['quantity'], 5)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert that staff users can modify item prices
        self.assertEqual(response.data['unit_price'], '100.00')

        # Assert that updating an item that is not in an order's item list
        # fails
        data['item'] = inventories[3].pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.data,
            {
                'item': ["This item doesn't exists in this order."]
            }
        )

        # Assert that updating items on a pending orders is allowed
        url: str = reverse('orders-update-item', args=[order1.pk])
        data['item'] = inventories[0].pk
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.data['quantity'], 5)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that updating items to a non created nor pending orders fails
        order1.approve(employee)  # APPROVED ORDER
        response = self.client.post(url, data, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # Assert that updating items to a non created nor pending orders fails
        order2.cancel(customer2.user)  # CANCELED ORDER
        url: str = reverse('orders-update-item', args=[order2.pk])
        response = self.client.post(url, data, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # Assert that updating items to a non created nor pending orders fails
        order3.reject(employee, 'A good reason')  # REJECTED ORDER
        url: str = reverse('orders-update-item', args=[order3.pk])
        response = self.client.post(url, data, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_update_order(self) -> None:
        """
        Ensure that the **OrderViewSet.update** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        order: Order = OrderFactory.create(customer=customer)

        # Request data
        post_data: Dict[str, Any] = OrderSerializer(order).data
        post_data['state'] = Order.OrderState.PENDING.choice_value
        patch_data = {
            'state': Order.OrderState.PENDING.choice_value
        }
        url: str = reverse('orders-detail', args=[order.pk])

        # Assert that customers cannot not update existing orders directly
        self.client.force_authenticate(user=customer.user)
        response = self.client.post(
            url,
            post_data,
            format='json'
        )  # POST request
        self.assertNotEqual(
            order.state,
            Order.OrderState.PENDING.choice_value
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        response = self.client.patch(
            url,
            patch_data,
            format='json'
        )  # PATCH request
        self.assertNotEqual(
            order.state,
            Order.OrderState.PENDING.choice_value
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Assert that even admins cannot not update existing orders directly
        self.client.force_authenticate(user=admin)
        response = self.client.post(
            url,
            post_data,
            format='json'
        )  # POST request
        self.assertNotEqual(
            order.state,
            Order.OrderState.PENDING.choice_value
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        response = self.client.patch(
            url,
            patch_data,
            format='json'
        )  # PATCH request
        self.assertNotEqual(
            order.state,
            Order.OrderState.PENDING.choice_value
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# noinspection PyUnresolvedReferences
class OrderItemViewSetTests(APITestCase):
    """
    Tests for the **OrderItemViewSet** class.
    """

    def test_list_order_items(self) -> None:
        """
        Ensure that the **OrderItemsViewSet.list** action works as expected.
        """
        # Test data
        admin: User = AdminFactory.create()
        customer: Customer = CustomerFactory.create()
        customer2: Customer = CustomerFactory.create()
        order: Order = OrderFactory.create(customer=customer)
        order1: Order = OrderFactory.create(customer=customer2)
        OrderItemFactory.create_batch(5, order=order)
        OrderItemFactory.create_batch(3, order=order1)

        # Request data
        url: str = reverse('order-items-list')

        # Assert that when a customer is logged on, he/she cannot see other
        # customer's order items
        self.client.force_authenticate(user=customer.user)
        response = self.client.get(url, format='json')

        self.assertEqual(len(response.data.get('order_items')), 5)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=customer2.user)
        response = self.client.get(url, format='json')

        self.assertEqual(len(response.data.get('order_items')), 3)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that when an employee is logged on, he/she can see all the
        # customers' order items
        self.client.force_authenticate(user=admin)
        response = self.client.get(url, format='json')

        self.assertEqual(len(response.data.get('order_items')), 8)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

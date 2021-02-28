from typing import List

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
from ..serializers import InventorySerializer, LimitedInventorySerializer
from ..apiviews import InventoryViewSet

from .factories import CustomerFactory, EmployeeFactory, InventoryFactory


# Constant

User = get_user_model()


# TestCases

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


class InventoryViewSetTests(APITestCase):
    """
    Tests for the **InventoryViewSet** class.
    """

    def test_list_inventory(self) -> None:
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
        Ensure that the **InventoryViewSet.list** action works as expected.
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

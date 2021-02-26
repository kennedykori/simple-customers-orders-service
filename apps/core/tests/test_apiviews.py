from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .factories import AdminFactory, UserFactory


# Constant

User = get_user_model()


# TestCases

class UserViewSetTests(APITestCase):
    """
    Tests for the **UserViewSet** class.
    """

    def test_create_user(self) -> None:
        """
        Ensure creating a user account works as expected.
        """
        url: str = reverse('users-list')
        data = {
            'username': 'user_x',
            'email': 'user_x@mail.test',
            'password': 'changeme'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_change_password(self) -> None:
        """
        Ensure that the **UserViewSet.change_password** action works as
        expected.
        """
        # Test data
        response_data = {'status': 'password changed'}
        secure_password = 'secure-PA55WORD!!!'
        secure_password1 = 'secure-PA55WORD1!!!'

        # Create test users
        admin: User = AdminFactory.create()
        user: User = UserFactory.create()
        user1: User = UserFactory.create()

        # Authenticate user
        self.client.force_authenticate(user=user)

        # Assert that the user can change the password
        url: str = reverse('users-change-password', args=[user.pk])
        data = {'new_password': secure_password}
        response = self.client.post(url, data, format='json')
        user.refresh_from_db()

        self.assertDictEqual(response.data, response_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.check_password(secure_password))

        # Assert that an admin can change the password of another user
        self.client.force_authenticate(user=admin)
        data = {'new_password': secure_password1}
        response = self.client.post(url, data, format='json')
        user.refresh_from_db()

        self.assertDictEqual(response.data, response_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.check_password(secure_password1))

        # Assert that a bad request fails
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, {'new_password': '1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that a non-admin can not change the password of another user
        self.client.force_authenticate(user=user1)
        data = {'new_password': secure_password}
        response = self.client.post(url, data, format='json')
        user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Assert that the password did not change
        self.assertFalse(user.check_password(secure_password))
        self.assertTrue(user.check_password(secure_password1))

    def test_change_staff_status(self) -> None:
        """
        Ensure that the **UserViewSet.change_staff_status** action works as
        expected.
        """
        # Test data
        response_data = {'is_staff': True}

        # Create test users
        admin: User = AdminFactory.create()
        user: User = UserFactory.create()

        # Authenticate user
        self.client.force_authenticate(user=user)

        # Assert that a non admin user cannot change his/her staff status
        url: str = reverse('users-change-staff-status', args=[user.pk])
        data = {'is_staff': True}
        response = self.client.post(url, data, format='json')
        user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(user.is_staff)

        # Assert that an admin can change a user's staff status
        self.client.force_authenticate(user=admin)
        response = self.client.post(url, data, format='json')
        user.refresh_from_db()
        self.assertDictEqual(response.data, response_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.is_staff)

        # Assert that a bad request fails
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

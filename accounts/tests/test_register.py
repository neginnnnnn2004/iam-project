from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User

class UserRegisterTest(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')

    def test_successful_register(self):
        valid_data1 = {
            'username': 'samira',
            'password': '60A9gvNT',
            'confirm_password': '60A9gvNT',
            'email': 'samira@test.com',
            'phone': '09100825689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }

        response = self.client.post(
            self.register_url,
            valid_data1,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        # Verification
        self.assertTrue(
            User.objects.filter(username='samira').exists()
        )

        valid_data2 = {
            'username': 'alireza',
            'password': 'hkhKaVPv',
            'confirm_password': 'hkhKaVPv',
            'email': 'alrz@test.com',
            'phone': '09123456789',
            'first_name': 'Alireza',
            'last_name': 'Jamee'
        }

        response = self.client.post(
            self.register_url,
            valid_data2,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        # Verification
        self.assertTrue(
            User.objects.filter(username='alireza').exists()
        )

    def test_unsuccessful_register_error_code_10(self):
        data = {
            'username': '11111',
            'password': '1234Aa@QqWw',
            'confirm_password': '1234Aa@QqWw',
            'email': 'dra@test.com',
            'phone': '09188325689',
            'first_name': 'Dara',
            'last_name': 'Zamani'
        }

        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 10)

    def test_unsuccessful_register_url_error_code_11(self):
        User.objects.create_user(
            username='dara80',
            password='1234Aa@QqWw'
        )

        data = {
            'username': 'dara80',
            'password': '123Aa@QqWw',
            'confirm_password': '123Aa@QqWw',
            'email': 'ddr@test.com',
            'phone': '09188325559',
            'first_name': 'Dara',
            'last_name': 'Moahmmadi'
        }

        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 11)

    def test_unsuccessful_error_code_12(self):
        data = {
            'username': '',
            'password': '',
            'confirm_password': '',
            'email': '',
            'phone': '',
            'first_name': '',
            'last_name': ''
        }

        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_error_code_13(self):
        data = {
            'username': 'dara',
            'password': '12341234',
            'confirm_password': '12341234',
            'email': 'ddr@test.com',
            'phone': '09188325559',
            'first_name': 'Dara',
            'last_name': 'Moahmmadi'
        }

        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 13)

    def test_unsuccessful_register_error_code_14(self):
        User.objects.create_user(
            username='test_user',
            password='Test@1234',
            phone='09111111111'
        )

        data = {
            'username': 'new_user',
            'password': 'Test@1234',
            'confirm_password': 'Test@1234',
            'email': 'new@test.com',
            'phone': '09111111111',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 14)

    def test_unsuccessful_register_error_code_15(self):
        User.objects.create_user(
            username='test_user2',
            password='Test@1234',
            email='existing@test.com'
        )

        data = {
            'username': 'new_user2',
            'password': 'Test@1234',
            'confirm_password': 'Test@1234',
            'email': 'existing@test.com',
            'phone': '09222222222',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 15)

    def test_unsuccessful_register_error_code_16_invalid_email(self):
        data = {
            'username': 'user_test',
            'password': 'Test@1234',
            'confirm_password': 'Test@1234',
            'email': 'invalid-email',
            'phone': '09333333333',
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 16)

    def test_unsuccessful_register_error_code_16_invalid_phone(self):
        data = {
            'username': 'user_test2',
            'password': 'Test@1234',
            'confirm_password': 'Test@1234',
            'email': 'user@test.com',
            'phone': '12345678911',
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 16)

    def test_unsuccessful_register_password_confirm_mismatch_error_code_17(self):
        data = {
            'username': 'mismatch_user',
            'password': 'ValidPass@1234',
            'confirm_password': 'DifferentPass@5678',
            'email': 'mismatch@test.com',
            'phone': '09123456789',
            'first_name': 'Mismatch',
            'last_name': 'Test'
        }

        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 17)

        # Check password mismatch error
        detail = response.data.get('detail', {})

        self.assertTrue(
            any(
                'match' in str(value).lower()
                or 'مطابقت' in str(value)
                for value in detail.values()
            ),
            'No password mismatch error found in detail'
        )

        # User must not be created
        self.assertFalse(
            User.objects.filter(username='mismatch_user').exists()
        )
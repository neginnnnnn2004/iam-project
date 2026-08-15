from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User
from django.utils import timezone

class UserLoginTest(APITestCase):

    def setUp(self):
        self.login_url = reverse('login')

    def test_successful_login(self):
        user = User.objects.create_user(
            username='dara',
            password='^5MN76f[',
            email='dara@test.com',
            phone='09100825689'
        )

        user.status = 'active'
        user.is_active = True
        user.save()

        data = {
            'username': 'dara',
            'password': '^5MN76f[',
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertIn('access_token', response.data)
        self.assertIn('refresh', response.data)

        # Second successful login
        user = User.objects.create_user(
            username='nima',
            password='r4-0X^1~',
            email='nima@test.com',
            phone='09188825689'
        )

        user.status = 'active'
        user.is_active = True
        user.save()

        data = {
            'username': 'nima',
            'password': 'r4-0X^1~',
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertIn('access_token', response.data)
        self.assertIn('refresh', response.data)

    def test_unsuccessful_login(self):
        # Invalid username
        user = User.objects.create_user(
            username='nima',
            password='r4-0X^1~',
            email='nima@test.com',
            phone='09188825689'
        )

        user.status = 'active'
        user.is_active = True
        user.save()

        data = {
            'username': 'nimaa',
            'password': 'r4-0X^1~'
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(response.data['error_code'], 20)

        # Invalid password
        user = User.objects.create_user(
            username='nima83',
            password='r450X^1~',
            email='nima83@test.com',
            phone='09168825689'
        )

        user.status = 'active'
        user.is_active = True
        user.save()

        data = {
            'username': 'nima83',
            'password': 'r4-0X^1~'
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(response.data['error_code'], 20)

        # Deleted user
        user = User.objects.create_user(
            username='nilan',
            password='r450X^1~',
            email='nilan@test.com',
            phone='09168826689'
        )

        user.is_active = True
        user.deleted_at = timezone.now()
        user.status = 'deleted'
        user.save()

        data = {
            'username': 'nilan',
            'password': 'r450X^1~'
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(response.data['error_code'], 20)

        # Pending user
        user = User.objects.create_user(
            username='asali',
            password='r450X^1~',
            email='asali@test.com',
            phone='09178826689'
        )

        user.status = 'pending'
        user.is_active = True
        user.save()

        data = {
            'username': 'asali',
            'password': 'r450X^1~'
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(response.data['error_code'], 21)

    def test_unsuccessful_bad_request(self):
        user = User.objects.create_user(
            username='negin',
            password='5MN76Ff',
            email='negin@test.com',
            phone='09100825689'
        )

        user.status = 'active'
        user.is_active = True
        user.save()

        # Empty password
        data = {
            'username': 'negin',
            'password': ''
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 10)

        # Missing password
        user = User.objects.create_user(
            username='dara',
            password='pass123'
        )

        user.status = 'active'
        user.is_active = True
        user.save()

        data = {
            'username': 'dara'
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 10)

        # Empty username and password
        data = {
            'username': '',
            'password': ''
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 10)

        # Username as list
        data = {
            'username': ['dara', 'nima'],
            'password': 'pass123'
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 10)

        # Password as object
        data = {
            'username': 'dara',
            'password': {
                'value': 'pass123'
            }
        }

        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(response.data['error_code'], 10)
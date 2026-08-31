from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from identity.models import User

class UserLoginTest(APITestCase):

    def setUp(self):
        self.login_url = reverse('login')

        self.user = User.objects.create_user(
            username='test_user',
            password='Strong123',
            email='test@test.com',
            phone='09123456789',
        )
        self.user.status = 'active'
        self.user.save()

    #successful_login_tsets
    def test_successful_login(self):
        data = {'username': 'test_user', 'password': 'Strong123'}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('access_token', response.data)
        self.assertIn('refresh',response.data)

        self.assertTrue(response.data['access_token'])
        self.assertTrue(response.data['refresh'])

    def test_successful_login_username_case_insensitive(self):
        data = {'username': 'TEST_USER', 'password': 'Strong123'}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('access_token', response.data)
        self.assertIn('refresh',response.data)

    def test_successful_login_username_with_spaces(self):
        data = {'username': '  test_user  ','password': 'Strong123', }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('access_token', response.data)
        self.assertIn('refresh', response.data)

    #unsuccessful_login_tsets
    #Validation Tests:
    def test_login_empty_username(self):
        data = {'username': '','password': 'Strong123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)
        self.assertIn('username',response.data['detail'])

    def test_login_empty_password(self):
        data = {'username': 'test_user','password': '',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)
        self.assertIn('password',response.data['detail'])

    def test_login_missing_username(self):
        data = {'password': 'Strong123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)
        self.assertIn('username',response.data['detail'])

    def test_login_missing_password(self):
        data = {'username': 'test_user',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)
        self.assertIn('password',response.data['detail'])

    def test_login_null_username(self):
        data = {'username': None,'password': 'Strong123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)
        self.assertIn('username',response.data['detail'])

    def test_login_null_password(self):
        data = {'username': 'test_user','password': None,}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)
        self.assertIn('password',response.data['detail'])

    #Invalid Credentials
    def test_login_wrong_password(self):
        data = {'username': 'test_user','password': 'WrongPassword123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'],20)
        self.assertIsNone(response.data['detail'])

    def test_login_wrong_username(self):
        data = {'username': 'unknown_user','password': 'Strong123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'],20)
        self.assertIsNone(response.data['detail'])

    def test_login_wrong_username_and_password(self):
        data = {'username': 'unknown_user','password': 'WrongPassword123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'],20)
        self.assertIsNone(response.data['detail'])

    # Deleted User
    def test_login_deleted_user(self):
        self.user.status = 'deleted'
        self.user.save()

        data = {'username': 'test_user','password': 'Strong123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'],20)
        self.assertIsNone(response.data['detail'])

    # Account Status
    def test_login_unverified_user(self):
        self.user.status = 'unverified'
        self.user.save()

        data = {'username': 'test_user','password': 'Strong123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'],21)
        self.assertIsNone(response.data['detail'])

    def test_login_pending_user(self):
        self.user.status = 'pending'
        self.user.save()

        data = {'username': 'test_user','password': 'Strong123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'],21)
        self.assertIsNone(response.data['detail'])

    def test_login_suspended_user(self):
        self.user.status = 'suspended'
        self.user.save()

        data = {'username': 'test_user','password': 'Strong123',}
        response = self.client.post(self.login_url,data,format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'],21)
        self.assertIsNone(response.data['detail'])
    #####################################################################
    def test_successful_login_returns_valid_access_token(self):
        data = {'username': 'test_user','password': 'Strong123',}
        response = self.client.post(self.login_url,data,format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access_token']
        token = AccessToken(access_token)
        self.assertEqual(int(token['user_id']),self.user.id)
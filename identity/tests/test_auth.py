from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User

class UserRegisterTest(APITestCase):
    def setUp(self):
        self.url = reverse('user-register')
    def test_successful_register(self):
        valid_data1 = {
            'username':"samira",
            'password':"8!4J8&kj",
            'email':"samira@test.com",
            'phone':"+989100825689",
            'first_name':"Samira",
            'last_name':"Mehrgo"
        }
        response = self.client.post(self.url, valid_data1, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        #verification
        self.assertTrue(User.objects.filter(username="samira").exists())

        valid_data2 = {
            'username':"alireza",
            'password':"!Mp4t4)4",
            'email':"alrz@test.com",
            'phone':"+989123456789",
            'first_name':"Alireza",
            'last_name':"Jamee"
        }
        response = self.client.post(self.url, valid_data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # verification
        self.assertTrue(User.objects.filter(username="alireza").exists())

    def test_unsuccessful_register(self):
        data = {
            'username': "user83",
            'password': "pass",
            'email': "invalid-email-format",
            'phone': "+123456789"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 16)


    def test_unsuccessful_error_code_11(self):
        User.objects.create_user(username='dara', password='old_pass')
        data = {
            'username': "dara",
            'password': "pa",
            'email': "dra@test.com",
            'phone': "+989188325689",
            'first_name': "Dara",
            'last_name': "Zamani"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],11)


        data = {
            'username': "",
            'password': "",
            'email': "",
            'phone': "",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

class LoginRegisterTest(APITestCase):
    def setUp(self):
        self.url = reverse('user-login')
    def test_successful(self):
        User.objects.create_user(username='dara', password='^5MN76f[', email='dara@test.com',phone='+989100825689')
        data = {
            'username':"dara",
            'password':"^5MN76f[",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)

        User.objects.create_user(username='nima', password='r4-0X^1~', email='nima@test.com',phone='+989188825689')
        data = {
            'username':"nima",
            'password':"r4-0X^1~",
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)

    def test_unsuccessful_wrong_pass(self):
        User.objects.create_user(username='dara', password='5MN76f', email='dara@test.com',phone='+989100825689')
        data = {'username': "dara", 'password': "passwrong"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], 13)

        User.objects.create_user(username='nima', password='r4-0X^1~', email='nima@test.com', phone='+989188825689')
        data = {'username': "nimaa", 'password': "r4-0X^1~"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], 13)

    def test_unsuccessful_bad_req(self):
        User.objects.create_user(username="dara", password="pass123")

        data = {'username': 'dara'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)

        data = {'username': '', 'password': ''}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)

        data = {'username': ['dara', 'nima'], 'password': 'pass123'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)

        data = {'username': 'dara', 'password': {'value': 'pass123'}}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)

class ProfileUpdateTest(APITestCase):
    def setUp(self):
        self.url = reverse('update-profile')

        self.user = User.objects.create_user(
            username='dara',
            password='^9*$0Z9p',
            first_name='Dara',
            last_name='Zamani',
        )

    def test_unauthorized_user_cannot_access(self):
        data = {"username": 'daraaa'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful_patch_update(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'first_name': 'Dana',
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # verification
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Dana')

    def test_successful_patch_update_and_password_hashing(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'first_name': 'Mohammad',
            'last_name': 'Rezaei',
            'password': 'S4=3no3='
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # verification
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Mohammad')
        self.assertEqual(self.user.last_name, 'Rezaei')
        self.assertTrue(self.user.check_password('S4=3no3='))

    def test_update_code_10_blank_or_whitespace_fields(self):
        self.client.force_authenticate(user=self.user)

        data = {'first_name': ''}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)

        data = {'last_name': '     '}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)

    def test_update_code_10_short_password(self):
        self.client.force_authenticate(user=self.user)

        data = {
            'password': 'short1'
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 14)
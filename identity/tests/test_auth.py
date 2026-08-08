from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User
from  django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

class UserRegisterTest(APITestCase):
    def setUp(self):
        self.url = reverse('user-register')
    def test_successful_register(self):
        valid_data1 = {
            'username':"samira",
            'password':"60A9gvNT",
            'confirm_password': "60A9gvNT",
            'email':"samira@test.com",
            'phone':"09100825689",
            'first_name':"Samira",
            'last_name':"Mehrgo"
        }
        response = self.client.post(self.url, valid_data1, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        #verification
        self.assertTrue(User.objects.filter(username="samira").exists())

        valid_data2 = {
            'username':"alireza",
            'password':"hkhKaVPv",
            'confirm_password': "hkhKaVPv",
            'email':"alrz@test.com",
            'phone':"09123456789",
            'first_name':"Alireza",
            'last_name':"Jamee"
        }
        response = self.client.post(self.url, valid_data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # verification
        self.assertTrue(User.objects.filter(username="alireza").exists())

    def test_unsuccessful_error_code_10(self):
        data = {
            'username': "11111",
            'password': "1234Aa@QqWw",
            'confirm_password': "1234Aa@QqWw",
            'email': "dra@test.com",
            'phone': "09188325689",
            'first_name': "Dara",
            'last_name': "Zamani"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)

    def test_unsuccessful_error_code_11(self):
        User.objects.create_user(username='dara', password='1234Aa@QqWw')
        data = {
            'username': "dara",
            'password': "123Aa@QqWw",
            'confirm_password': "123Aa@QqWw",
            'email': "ddr@test.com",
            'phone': "09188325559",
            'first_name': "Dara",
            'last_name': "Moahmmadi"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 11)

    def test_unsuccessful_error_code_12(self):
        data = {
            'username': "",
            'password':"" ,
            'confirm_password': "",
            'email': "",
            'phone': "",
            'first_name': "",
            'last_name': ""
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_error_code_13(self):
       data = {
           'username': "dara",
           'password': "12341234",
           'confirm_password': "12341234",
           'email': "ddr@test.com",
           'phone': "09188325559",
           'first_name': "Dara",
           'last_name': "Moahmmadi"
       }
       response = self.client.post(self.url, data, format='json')
       self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
       self.assertEqual(response.data['error_code'], 13)

    def test_unsuccessful_error_code_14(self):
        User.objects.create_user(
            username='test_user',
            password='Test@1234',
            phone='09111111111'
        )

        data = {
            'username': "new_user",
            'password': "Test@1234",
            'confirm_password': "Test@1234",
            'email': "new@test.com",
            'phone': "09111111111",
            'first_name': "New",
            'last_name': "User"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 14)

    def test_unsuccessful_error_code_15(self):
        User.objects.create_user(
            username='test_user2',
            password='Test@1234',
            email='existing@test.com'
        )

        data = {
            'username': "new_user2",
            'password': "Test@1234",
            'confirm_password': "Test@1234",
            'email': "existing@test.com",
            'phone': "09222222222",
            'first_name': "New",
            'last_name': "User"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 15)

    def test_unsuccessful_error_code_16_invalid_email(self):
        data = {
            'username': "user_test",
            'password': "Test@1234",
            'confirm_password': "Test@1234",
            'email': "invalid-email",
            'phone': "09333333333",
            'first_name': "Test",
            'last_name': "User"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 16)

    def test_unsuccessful_error_code_16_invalid_phone(self):
        data = {
            'username': "user_test2",
            'password': "Test@1234",
            'confirm_password': "Test@1234",
            'email': "user@test.com",
            'phone': "123456789",
            'first_name': "Test",
            'last_name': "User"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 16)

class LoginRegisterTest(APITestCase):
    def setUp(self):
        self.url = reverse('user-login')
    def test_successful_login(self):
        user=User.objects.create_user(username='dara', password='^5MN76f[', email='dara@test.com',phone='09100825689')
        user.status = 'active'
        user.is_active = True
        user.save()

        data = {
            'username': "dara",
            'password': "^5MN76f[",
        }
        response = self.client.post(self.url, data, format='json')

        print(f"Status: {response.status_code}")
        print(f"Data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh', response.data)

        user = User.objects.create_user(username='nima', password='r4-0X^1~', email='nima@test.com',phone='09188825689')
        user.status = 'active'
        user.is_active = True
        user.save()
        data = {
            'username':"nima",
            'password':"r4-0X^1~",
        }
        response = self.client.post(self.url, data, format='json')
        print(f"Status: {response.status_code}")
        print(f"Data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh', response.data)


    def test_unsuccessful_login(self):
        user=User.objects.create_user(username='nima', password='r4-0X^1~', email='nima@test.com', phone='09188825689')
        user.status = 'active'
        user.is_active = True
        user.save()
        data = {'username': "nimaa", 'password': "r4-0X^1~"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], 20)

        user=User.objects.create_user(username='nima83', password='r450X^1~', email='nima83@test.com',phone='09168825689')
        user.status = 'active'
        user.is_active = True
        user.save()
        data = {'username': "nima83", 'password': "r4-0X^1~"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], 20)

        user=User.objects.create_user(username='nilan', password='r450X^1~', email='nilan@test.com',phone='09168826689')
        user.is_active = True
        user.deleted_at = timezone.now()
        user.status = 'deleted'
        user.save()
        data = {'username': "nilan", 'password': "r450X^1~"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], 20)

        user = User.objects.create_user(username='asali', password='r450X^1~', email='asali@test.com',phone='09178826689')
        user.status = 'pending'
        user.is_active = True
        user.save()
        data = {'username': "asali", 'password': "r450X^1~"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error_code'], 21)

    def test_unsuccessful_bad_req(self):
        user=User.objects.create_user(username='negin', password='5MN76Ff' ,email='negin@test.com',phone='09100825689')
        user.status = 'active'
        user.is_active = True
        user.save()
        data = {'username': "negin", 'password': ""}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)

        user=User.objects.create_user(username="dara", password="pass123")
        user.status = 'active'
        user.is_active = True
        user.save()

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

        self.user = User.objects.create_user(username='test_user',email="test_user11@test.com",password='Test@1234',phone='09100825689', first_name='Test',last_name='User')
        self.user.status = 'active'
        self.user.is_active = True
        self.user.save()

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')


    def test_successful_update_phone(self):
        data = {
            'phone': '09123456789'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['phone'], '09123456789')

        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, '09123456789')

    def test_successful_update_first_name(self):
        data = {
            'first_name': 'NewName'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['first_name'], 'NewName')

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewName')

    def test_successful_update_multiple_fields(self):
        data = {
            'first_name': 'NewFirstName',
            'last_name': 'NewLastName',
            'phone': '09123456789'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewFirstName')
        self.assertEqual(self.user.last_name, 'NewLastName')
        self.assertEqual(self.user.phone, '09123456789')

    def test_successful_update_password(self):
        data = {
            'password': 'NewPassword@1234',
            'confirm_password': 'NewPassword@1234',
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword@1234'))
        self.assertFalse(self.user.check_password('Test@1234'))


    def test_update_phone_invalid_format(self):
        data = {
            'phone': '123456789'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 32)
        self.assertIn('phone', response.data['detail'])

    def test_update_phone_invalid_format_without_zero(self):
        data = {
            'phone': '9123456789'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 32)

    def test_update_phone_short_number(self):
        data = {
            'phone': '091'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 32)

    def test_update_phone_long_number(self):
        data = {
            'phone': '09123456789555550'
        }
        response = self.client.patch(self.url, data, format='json')

    def test_update_phone_duplicate(self):
        User.objects.create_user(
            username='other_user2',
            password='Other2@1234',
            phone='09555555555'
        )

        data = {
            'phone': '09555555555'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 32)
        self.assertIn('phone', response.data['detail'])

    def test_update_password_invalid_weak(self):
        data = {
            'password': '1234'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 30)
        self.assertIn('password', response.data['detail'])

    def test_update_password_common(self):
        data = {
            'password': 'password123'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 30)

    def test_update_password_similar_to_username(self):
        data = {
            'password': 'testuser123'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 30)

    def test_update_empty_data(self):
        data = {}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_phone_to_existing_own_phone(self):
        data = {
            'phone': '09100825689'
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_update_multiple_fields_with_one_invalid(self):
        """تست بروزرسانی چند فیلد که یکی نامعتبر است"""
        data = {
            'first_name': 'ValidName',
            'phone': '9123456789'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 32)

        self.user.refresh_from_db()
        self.assertNotEqual(self.user.first_name, 'ValidName')

    def test_update_all_fields_successfully(self):
        data = {
            'first_name': 'NewFirst',
            'last_name': 'NewLast',
            'phone': '09999999999'
        }
        response = self.client.patch(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewFirst')
        self.assertEqual(self.user.last_name, 'NewLast')
        self.assertEqual(self.user.phone, '09999999999')


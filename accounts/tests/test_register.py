from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User

class UserRegisterTest(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')

    #successful_register_test
    def test_successful_register_all_valid_fields(self):
        valid_data1 = {
            'username': 'test_user_1',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user1@test.com',
            'phone': '09100825689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data1, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='test_user_1').exists())

        valid_data2 = {
            'username': 'test_user_2',
            'password': '9BTGbels',
            'confirm_password': '9BTGbels',
            'email': 'user2@test.com',
            'phone': '09100825659',
            'first_name': 'Sima',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='test_user_2').exists())

    def test_successful_register_without_first_name(self):
        valid_data3 = {
            'username': 'test_user_3',
            'password': 'Z1LWIX6p',
            'confirm_password': 'Z1LWIX6p',
            'email': 'user3@test.com',
            'phone': '09140825689',
            'first_name': '',
            'last_name': 'Fani'
        }
        response = self.client.post(self.register_url, valid_data3, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='test_user_3').exists())

    def test_successful_register_without_last_name(self):
        valid_data4 = {
            'username': 'test_user_4',
            'password': 'Iot8Ckgs',
            'confirm_password': 'Iot8Ckgs',
            'email': 'user4@test.com',
            'phone': '09940825689',
            'first_name': 'Parsa',
            'last_name': ''
        }
        response = self.client.post(self.register_url, valid_data4, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='test_user_4').exists())

    def test_successful_register_without_last_name_or_first_name(self):
        valid_data5 = {
            'username': 'test_user_5',
            'password': 'Iot8Ckgs',
            'confirm_password': 'Iot8Ckgs',
            'email': 'user5@test.com',
            'phone': '09940865689',
            'first_name': '',
            'last_name': ''
        }
        response = self.client.post(self.register_url, valid_data5, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='test_user_5').exists())

    def test_successful_register_username_with_five_character(self):
        valid_data6 = {
            'username': 'test6',
            'password': 'Iot8Ckgs',
            'confirm_password': 'Iot8Ckgs',
            'email': 'user6@test.com',
            'phone': '09944465689',
            'first_name': 'Naser',
            'last_name': 'Ghannad'
        }
        response = self.client.post(self.register_url, valid_data6, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='test6').exists())

    def test_successful_register_username_with_twenty_character(self):
        valid_data7 = {
            'username': "test_user_0123456789",
            'password': 'Iot8Ckgs',
            'confirm_password': 'Iot8Ckgs',
            'email': 'user7@test.com',
            'phone': '09844465689',
            'first_name': 'Naser',
            'last_name': 'Ghannad'
        }
        response = self.client.post(self.register_url, valid_data7, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='test_user_0123456789').exists())

    def test_successful_register_username_with_capital_character(self):
        valid_data8 = {
            'username': 'TEST_USER_8',
            'password': 'Iot8Ckgs',
            'confirm_password': 'Iot8Ckgs',
            'email': 'user8@test.com',
            'phone': '09100355083',
            'first_name': 'Naser',
            'last_name': 'Ghannad'
        }
        response = self.client.post(self.register_url, valid_data8, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='test_user_8').exists())

    def test_successful_register_email_with_capital_character(self):
        valid_data = {
            'username': 'test_user_10',
            'password': 'Iot8Ckgs',
            'confirm_password': 'Iot8Ckgs',
            'email': 'USER10@TEST.COM',
            'phone': '09844465889',
            'first_name': 'Naser',
            'last_name': 'Ghannad'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='user10@test.com').exists())

    def test_register_phone_with_spaces(self):
        valid_data10 = {
            'username': 'test_user',
            'password': '60A9gvNT',
            'confirm_password': '60A9gvNT',
            'email': 'user@test.com',
            'phone': ' 09100825389 ',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data10, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(phone='09100825389').exists())

    #unsuccessful_register_test(empty fields) -> error_code 12
    def test_unsuccessful_register_empty_username(self):
        valid_data = {
            'username': '',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user1@test.com',
            'phone': '09100825689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_empty_password(self):
        valid_data = {
            'username': 'test_1',
            'password': '',
            'confirm_password': '2eHRKaQy',
            'email': 'user1@test.com',
            'phone': '09106625689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_empty_confirm_password(self):
        valid_data = {
            'username': 'test_2',
            'password': '2eHRKaQy',
            'confirm_password': '',
            'email': 'user1@test.com',
            'phone': '09100898689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_empty_email(self):
        valid_data = {
            'username': 'test_3',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': '',
            'phone': '09100898689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_empty_phone(self):
        valid_data = {
            'username': 'test_4',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'test11@gmail.com',
            'phone': '',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    #unsuccessful_register_test(missing fields) -> error_code 12
    def test_unsuccessful_register_missing_username(self):
        valid_data = {
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user1@test.com',
            'phone': '09100825689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_missing_password(self):
        valid_data = {
            'username': 'test_1',
            'confirm_password': '2eHRKaQy',
            'email': 'user1@test.com',
            'phone': '09106625689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_missing_confirm_password(self):
        valid_data = {
            'username': 'test_2',
            'password': '2eHRKaQy',
            'email': 'user1@test.com',
            'phone': '09100898689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_missing_email(self):
        valid_data = {
            'username': 'test_3',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'phone': '09100898689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_missing_phone(self):
        valid_data = {
            'username': 'test_4',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'test11@gmail.com',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)


    #unsuccessful_register_test(null fields) -> error_code 12
    def test_unsuccessful_register_null_username(self):
        valid_data = {
            'username': None,
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user1@test.com',
            'phone': '09100825689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_null_password(self):
        valid_data = {
            'username': 'test_1',
            'password': None,
            'confirm_password': '2eHRKaQy',
            'email': 'user1@test.com',
            'phone': '09106625689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_null_confirm_password(self):
        valid_data = {
            'username': 'test_2',
            'password': '2eHRKaQy',
            'confirm_password': None,
            'email': 'user1@test.com',
            'phone': '09100898689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_null_email(self):
        valid_data = {
            'username': 'test_3',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': None,
            'phone': '09100898689',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)

    def test_unsuccessful_register_null_phone(self):
        valid_data = {
            'username': 'test_4',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'test11@gmail.com',
            'phone': None,
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 12)
        #########################################################################

    #test business logic
    def test_unsuccessful_register_username_less_than_five_characters(self):
        valid_data = {
        'username': 'abc',
        'password': '2eHRKaQy',
        'confirm_password': '2eHRKaQy',
        'email': 'user@test.com',
        'phone': '09879968021',
        }
        response = self.client.post(self.register_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)
        self.assertIn('username', response.data['detail'])

    def test_unsuccessful_register_username_more_than_twenty_characters(self):
        data = {
            'username': 'a' * 21,
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)
        self.assertIn('username', response.data['detail'])

    def test_unsuccessful_register_username_only_digits(self):
        data = {
            'username': '123456',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)
        self.assertIn('username', response.data['detail'])

    def test_unsuccessful_register_duplicate_username(self):
        User.objects.create_user(
            username='test_user',
            password='Existing123'
        )

        data = {
            'username': 'test_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'new@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 11)
        self.assertIn('username', response.data['detail'])

    def test_unsuccessful_register_duplicate_username_case_insensitive(self):
        User.objects.create_user(
            username='test_user',
            password='Existing123'
        )

        data = {
            'username': 'TEST_USER',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'new@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 11)
        self.assertIn('username', response.data['detail'])

    def test_unsuccessful_register_password_less_than_eight_characters(self):
        data = {
            'username': 'test_user',
            'password': 'Ab123',
            'confirm_password': 'Ab123',
            'email': 'user@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 13)
        self.assertIn('password', response.data['detail'])

    def test_unsuccessful_register_weak_password(self):
        data = {
            'username': 'test_user',
            'password': '12345678',
            'confirm_password': '12345678',
            'email': 'user@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 13)
        self.assertIn('password', response.data['detail'])

    def test_unsuccessful_register_password_confirmation_mismatch(self):
        data = {
            'username': 'test_user',
            'password': '2eHRKaQy',
            'confirm_password': 'Different123',
            'email': 'user@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 17)
        self.assertIn('confirm_password', response.data['detail'])

    def test_unsuccessful_register_invalid_email(self):
        data = {
            'username': 'test_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'invalid-email',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 16)
        self.assertIn('email', response.data['detail'])

    def test_unsuccessful_register_duplicate_email(self):
        User.objects.create_user(
            username='existing_user',
            password='Existing123',
            email='user@test.com'
        )

        data = {
            'username': 'new_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 15)
        self.assertIn('email', response.data['detail'])

    def test_unsuccessful_register_duplicate_email_case_insensitive(self):
        User.objects.create_user(
            username='existing_user',
            password='Existing123',
            email='user@test.com'
        )

        data = {
            'username': 'new_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'USER@TEST.COM',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 15)
        self.assertIn('email', response.data['detail'])

    def test_unsuccessful_register_invalid_phone_format(self):
        data = {
            'username': 'test_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '12345678901',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 16)
        self.assertIn('phone', response.data['detail'])

    def test_unsuccessful_register_phone_less_than_eleven_digits(self):
        data = {
            'username': 'test_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '0912345678',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 16)
        self.assertIn('phone', response.data['detail'])

    def test_unsuccessful_register_phone_more_than_eleven_digits(self):
        data = {
            'username': 'test_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '091234567890',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 16)
        self.assertIn('phone', response.data['detail'])

    def test_unsuccessful_register_duplicate_phone(self):
        User.objects.create_user(
            username='existing_user',
            password='Existing123',
            phone='09123456789'
        )

        data = {
            'username': 'new_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'new@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 14)
        self.assertIn('phone', response.data['detail'])

    #Additional tests
    def test_successful_register_username_with_spaces(self):
        data = {
            'username': '  Test_User  ',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            User.objects.filter(username='test_user').exists()
        )

    def test_password_is_hashed_after_registration(self):
        data = {
            'username': 'test_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username='test_user')

        self.assertNotEqual(user.password, '2eHRKaQy')
        self.assertTrue(user.check_password('2eHRKaQy'))

    def test_confirm_password_is_not_saved(self):
        data = {
            'username': 'test_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '09123456789',
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username='test_user')

        self.assertFalse(hasattr(user, 'confirm_password'))

    def test_successful_register_creates_user_with_correct_data(self):
        data = {
            'username': 'test_user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '09123456789',
            'first_name': 'Samira',
            'last_name': 'Mehrgo'
        }

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username='test_user')

        self.assertEqual(user.email, 'user@test.com')
        self.assertEqual(user.phone, '09123456789')
        self.assertEqual(user.first_name, 'Samira')
        self.assertEqual(user.last_name, 'Mehrgo')
        self.assertTrue(user.check_password('2eHRKaQy'))

    def test_unsuccessful_register_username_with_invalid_characters(self):
        data = {
            'username': 'test@user',
            'password': '2eHRKaQy',
            'confirm_password': '2eHRKaQy',
            'email': 'user@test.com',
            'phone': '09123456789',
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

        self.assertIn('username', response.data['detail'])


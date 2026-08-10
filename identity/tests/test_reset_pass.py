from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User, Role
from identity.utils import create_user_backup_codes

class UserResetPasswordTest(APITestCase):
    def setUp(self):

        self.regular_role = Role.objects.create(
            code='regular',
            title='کاربر معمولی',
            level = 20 ,
            is_system = True,
        )

        self.target_user = User.objects.create_user(
            username="normal_user",
            password="password123",
            email="normal@test.com",
            phone="09333333333",
            status="active",
            role=self.regular_role
        )

        self.pending_user = User.objects.create_user(
            username="pending_user",
            password="password123",
            email="pending@test.com",
            phone="09353333333",
            status="pending",
            role=self.regular_role
        )

        # Generate backup codes for target user
        self.target_backup_codes = create_user_backup_codes(
            self.target_user,
            count=8
        )

        # Generate backup codes for pending user
        self.pending_backup_codes = create_user_backup_codes(
            self.pending_user,
            count=8
        )

        self.reset_password_url = reverse('reset_password')

        self.assign_role_url = lambda pk: reverse(
            'assign-users-role',
            kwargs={'pk': pk}
        )

        self.manage_status_url = lambda pk: reverse(
            'manage-user-status',
            kwargs={'pk': pk}
        )

        self.activation_url = lambda pk: reverse(
            'is-active',
            kwargs={'pk': pk}
        )

    def test_reset_password_active_user_success(self):
        new_password = "NewPassword123!"

        data = {
            "username": self.target_user.username,
            "backup_code": self.target_backup_codes[0],
            "new_password": new_password,
            "confirm_password": new_password,
        }

        response = self.client.post( self.reset_password_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK )

        self.assertEqual(response.data["message"]["en"],"Your password has been changed successfully. You can now log in.")

        self.assertTrue(response.data["show_popup"] )

        self.assertIn("new_backup_code",response.data)

        self.assertTrue(response.data["new_backup_code"])

        # Check password was actually changed
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password(new_password))
        self.assertFalse(self.target_user.check_password("password123"))

    def test_reset_password_pending_user_unsuccess(self):
        new_password = "NewPassword123!"

        data = {
            "username": self.pending_user.username,
            "backup_code": self.target_backup_codes[1],
            "new_password": new_password,
            "confirm_password": new_password,
        }

        response = self.client.post( self.reset_password_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST )

        self.assertEqual(response.data["error_code"] , 75)
        self.assertEqual(
            response.data["message"]["en"],
            "The provided information or backup code is invalid."
        )

        self.assertEqual(
            response.data["message"]["fa"],
            "اطلاعات وارد شده یا کد پشتیبان معتبر نیست."
        )

        # Password must NOT be changed
        self.pending_user.refresh_from_db()
        self.assertTrue(self.pending_user.check_password('password123'))
        self.assertFalse(self.pending_user.check_password(new_password))

    def test_reset_password_unsuccess_with_Invalid_backup_code(self):
        new_password = "NewPassword123!"

        data = {
            "username": self.pending_user.username,
            "backup_code": 1258555,
            "new_password": new_password,
            "confirm_password": new_password,
        }

        response = self.client.post( self.reset_password_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST )

        self.assertEqual(response.data["error_code"] , 75)
        self.assertEqual(
            response.data["message"]["en"],
            "The provided information or backup code is invalid."
        )

        self.assertEqual(
            response.data["message"]["fa"],
            "اطلاعات وارد شده یا کد پشتیبان معتبر نیست."
        )

        # Password must NOT be changed
        self.pending_user.refresh_from_db()
        self.assertTrue(self.pending_user.check_password('password123'))
        self.assertFalse(self.pending_user.check_password(new_password))

    def test_reset_password_nonexistent_user(self):

        data = {
            "username": "user_does_not_exist",
            "backup_code": "INVALID1",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error_code"],
            75
        )

        self.assertEqual(
            response.data["message"]["en"],
            "The provided information or backup code is invalid."
        )

    def test_reset_password_confirmation_mismatch(self):

        data = {
            "username": self.target_user.username,
            "backup_code": self.target_backup_codes[0],
            "new_password": "NewPassword123!",
            "confirm_password": "DifferentPassword123!",
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error_code"],
            10
        )

        self.assertIn(
            "confirm_password",
            response.data["detail"]
        )

        self.target_user.refresh_from_db()

        self.assertTrue(
            self.target_user.check_password("password123")
        )

    def test_reset_password_weak_password(self):

        weak_password = "12345678"

        data = {
            "username": self.target_user.username,
            "backup_code": self.target_backup_codes[0],
            "new_password": weak_password,
            "confirm_password": weak_password,
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error_code"],
            10
        )

        self.assertIn(
            "new_password",
            response.data["detail"]
        )

        self.target_user.refresh_from_db()

        self.assertTrue(
            self.target_user.check_password("password123")
        )

    def test_reset_password_empty_username(self):

        data = {
            "username": "",
            "backup_code": self.target_backup_codes[0],
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error_code"],
            10
        )

    def test_reset_password_empty_backup_code(self):

        data = {
            "username": self.target_user.username,
            "backup_code": "",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error_code"],
            10
        )

    def test_reset_password_empty_new_password(self):

        data = {
            "username": self.target_user.username,
            "backup_code": self.target_backup_codes[0],
            "new_password": "",
            "confirm_password": "",
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error_code"],
            10
        )

    def test_reset_password_empty_confirm_password(self):

        data = {
            "username": self.target_user.username,
            "backup_code": self.target_backup_codes[0],
            "new_password": "NewPassword123!",
            "confirm_password": "",
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error_code"],
            10
        )


    def test_reset_password_missing_fields(self):

        response = self.client.post(
            self.reset_password_url,
            {},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error_code"],
            10
        )

        self.assertIn(
            "username",
            response.data["detail"]
        )

        self.assertIn(
            "backup_code",
            response.data["detail"]
        )

        self.assertIn(
            "new_password",
            response.data["detail"]
        )

        self.assertIn(
            "confirm_password",
            response.data["detail"]
        )

    def test_reset_password_username_case_insensitive(self):

        new_password = "NewPassword123!"

        data = {
            "username": "NORMAL_USER",
            "backup_code": self.target_backup_codes[0],
            "new_password": new_password,
            "confirm_password": new_password,
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.target_user.refresh_from_db()

        self.assertTrue(
            self.target_user.check_password(new_password)
        )

    def test_backup_code_is_single_use(self):

        backup_code = self.target_backup_codes[0]

        first_password = "NewPassword123!"

        first_data = {
            "username": self.target_user.username,
            "backup_code": backup_code,
            "new_password": first_password,
            "confirm_password": first_password,
        }

        # First use
        first_response = self.client.post(
            self.reset_password_url,
            first_data,
            format="json"
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK
        )

        # Try to use the same code again
        second_password = "AnotherPassword123!"

        second_data = {
            "username": self.target_user.username,
            "backup_code": backup_code,
            "new_password": second_password,
            "confirm_password": second_password,
        }

        second_response = self.client.post(
            self.reset_password_url,
            second_data,
            format="json"
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            second_response.data["error_code"],
            75
        )

        # The second password must NOT be applied
        self.target_user.refresh_from_db()

        self.assertTrue(
            self.target_user.check_password(first_password)
        )

        self.assertFalse(
            self.target_user.check_password(second_password)
        )

    def test_new_backup_code_is_generated(self):

        old_backup_code = self.target_backup_codes[0]

        data = {
            "username": self.target_user.username,
            "backup_code": old_backup_code,
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        new_backup_code = response.data["new_backup_code"]

        self.assertIsNotNone(
            new_backup_code
        )

        self.assertTrue(
            new_backup_code
        )

        self.assertNotEqual(
            new_backup_code,
            old_backup_code
        )


    def test_returned_backup_code_can_be_used(self):

        first_password = "NewPassword123!"

        first_data = {
            "username": self.target_user.username,
            "backup_code": self.target_backup_codes[0],
            "new_password": first_password,
            "confirm_password": first_password,
        }

        first_response = self.client.post(
            self.reset_password_url,
            first_data,
            format="json"
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK
        )

        new_backup_code = first_response.data["new_backup_code"]

        # Use the newly generated backup code
        second_password = "AnotherPassword123!"

        second_data = {
            "username": self.target_user.username,
            "backup_code": new_backup_code,
            "new_password": second_password,
            "confirm_password": second_password,
        }

        second_response = self.client.post(
            self.reset_password_url,
            second_data,
            format="json"
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK
        )

        self.target_user.refresh_from_db()

        self.assertTrue(
            self.target_user.check_password(second_password)
        )

        self.assertFalse(
            self.target_user.check_password(first_password)
        )


    def test_backup_code_not_consumed_when_password_is_invalid(self):

        backup_code = self.target_backup_codes[0]

        data = {
            "username": self.target_user.username,
            "backup_code": backup_code,
            "new_password": "12345678",
            "confirm_password": "12345678",
        }

        response = self.client.post(
            self.reset_password_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        # Try the same backup code again with a valid password
        valid_password = "NewPassword123!"

        second_data = {
            "username": self.target_user.username,
            "backup_code": backup_code,
            "new_password": valid_password,
            "confirm_password": valid_password,
        }

        second_response = self.client.post(
            self.reset_password_url,
            second_data,
            format="json"
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK
        )


    def test_invalid_backup_code_does_not_consume_valid_backup_code(self):

        valid_backup_code = self.target_backup_codes[0]

        invalid_data = {
            "username": self.target_user.username,
            "backup_code": "INVALID1",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = self.client.post(
            self.reset_password_url,
            invalid_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        # The real backup code should still work
        valid_data = {
            "username": self.target_user.username,
            "backup_code": valid_backup_code,
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = self.client.post(
            self.reset_password_url,
            valid_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

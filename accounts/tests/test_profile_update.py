from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from identity.models import User


class ProfileUpdateTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="OldPassword123",
            email="test@example.com",
            phone="09123456789",
            first_name="Test",
            last_name="User",
        )

        self.profile_url = reverse("profile_update")

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    # ---------------------------------------------------------
    # 1. Successful profile update
    # ---------------------------------------------------------

    def test_successful_profile_update(self):
        data = {
            "first_name": "Ali",
            "last_name": "Ahmadi",
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "Ali")
        self.assertEqual(self.user.last_name, "Ahmadi")

    # ---------------------------------------------------------
    # 2. Update only first name
    # ---------------------------------------------------------

    def test_update_first_name_only(self):
        data = {
            "first_name": "NewName"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "NewName")
        self.assertEqual(self.user.last_name, "User")

    # ---------------------------------------------------------
    # 3. Update only last name
    # ---------------------------------------------------------

    def test_update_last_name_only(self):
        data = {
            "last_name": "NewLastName"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(self.user.last_name, "NewLastName")
        self.assertEqual(self.user.first_name, "Test")

    # ---------------------------------------------------------
    # 4. Update phone successfully
    # ---------------------------------------------------------

    def test_successful_phone_update(self):
        data = {
            "phone": "09987654321"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.phone,
            "09987654321"
        )

    # ---------------------------------------------------------
    # 5. Update password successfully
    # ---------------------------------------------------------

    def test_successful_password_update(self):
        data = {
            "password": "NewPassword123",
            "confirm_password": "NewPassword123",
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("NewPassword123")
        )

        self.assertFalse(
            self.user.check_password("OldPassword123")
        )

    # ---------------------------------------------------------
    # 6. Password confirmation mismatch
    # ---------------------------------------------------------

    def test_unsuccessful_password_mismatch(self):
        data = {
            "password": "NewPassword123",
            "confirm_password": "DifferentPassword123",
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "confirm_password",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 7. Password without confirm_password
    # ---------------------------------------------------------

    def test_unsuccessful_password_without_confirmation(self):
        data = {
            "password": "NewPassword123"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "confirm_password",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 8. confirm_password without password
    # ---------------------------------------------------------

    def test_unsuccessful_confirmation_without_password(self):
        data = {
            "confirm_password": "NewPassword123"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "password",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 9. Invalid phone format
    # ---------------------------------------------------------

    def test_unsuccessful_invalid_phone(self):
        data = {
            "phone": "123456789"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "phone",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 10. Phone with more than 11 digits
    # ---------------------------------------------------------

    def test_unsuccessful_phone_more_than_11_digits(self):
        data = {
            "phone": "091234567890"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "phone",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 11. Phone with less than 11 digits
    # ---------------------------------------------------------

    def test_unsuccessful_phone_less_than_11_digits(self):
        data = {
            "phone": "0912345678"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "phone",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 12. Duplicate phone number
    # ---------------------------------------------------------

    def test_unsuccessful_duplicate_phone(self):
        User.objects.create_user(
            username="anotheruser",
            password="Password123",
            email="another@example.com",
            phone="09111111111",
        )

        data = {
            "phone": "09111111111"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "phone",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 13. User can keep their own phone number
    # ---------------------------------------------------------

    def test_user_can_keep_own_phone_number(self):
        data = {
            "phone": "09123456789"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.phone,
            "09123456789"
        )

    # ---------------------------------------------------------
    # 14. Empty password should not change password
    # ---------------------------------------------------------

    def test_empty_password_does_not_change_password(self):
        data = {
            "password": "",
            "confirm_password": "",
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("OldPassword123")
        )

    # ---------------------------------------------------------
    # 15. Update all profile fields together
    # ---------------------------------------------------------

    def test_update_all_profile_fields(self):
        data = {
            "first_name": "NewFirstName",
            "last_name": "NewLastName",
            "phone": "09876543210",
            "password": "NewPassword123",
            "confirm_password": "NewPassword123",
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "NewFirstName"
        )

        self.assertEqual(
            self.user.last_name,
            "NewLastName"
        )

        self.assertEqual(
            self.user.phone,
            "09876543210"
        )

        self.assertTrue(
            self.user.check_password("NewPassword123")
        )

    # ---------------------------------------------------------
    # 16. Unauthenticated user cannot update profile
    # ---------------------------------------------------------

    def test_unauthenticated_user_cannot_update_profile(self):
        self.client.credentials()

        data = {
            "first_name": "Hacker"
        }

        response = self.client.patch(
            self.profile_url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
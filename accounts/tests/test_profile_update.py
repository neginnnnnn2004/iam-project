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
    # 6. Password confirmation mismatch -> error_code 32
    #    (raised in ProfileUpdateSerializer.validate(), keyed
    #    to 'confirm_password', caught by the `elif
    #    'confirm_password' in errors` branch in the view)
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

        self.assertEqual(response.data['error_code'], 32)

        self.assertIn(
            "confirm_password",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 7. Password without confirm_password -> error_code 32
    #    (raised in validate(), keyed to 'confirm_password')
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

        self.assertEqual(response.data['error_code'], 32)

        self.assertIn(
            "confirm_password",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 8. confirm_password without password -> error_code 30
    #    (raised in validate(), keyed to 'password'; the view's
    #    `if 'password' in errors` branch fires first)
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

        self.assertEqual(response.data['error_code'], 30)

        self.assertIn(
            "password",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 8b. Weak password rejected by Django's password validators
    #     (validate_password() -> django's validate_password())
    #     -> error_code 30
    # ---------------------------------------------------------

    def test_unsuccessful_weak_password(self):
        data = {
            "password": "12345678",
            "confirm_password": "12345678",
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

        self.assertEqual(response.data['error_code'], 30)

        self.assertIn(
            "password",
            response.data['detail']
        )

        # password must remain unchanged
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPassword123"))

    # ---------------------------------------------------------
    # 8c. Password shorter than the field's min_length=8
    #     (field-level validation, not validate_password())
    #     -> error_code 30
    # ---------------------------------------------------------

    def test_unsuccessful_password_too_short(self):
        data = {
            "password": "Ab1",
            "confirm_password": "Ab1",
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

        self.assertEqual(response.data['error_code'], 30)

        self.assertIn(
            "password",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 9. Invalid phone format -> error_code 31
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

        self.assertEqual(response.data['error_code'], 31)

        self.assertIn(
            "phone",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 10. Phone with more than 11 digits -> error_code 31
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

        self.assertEqual(response.data['error_code'], 31)

        self.assertIn(
            "phone",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 11. Phone with less than 11 digits -> error_code 31
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

        self.assertEqual(response.data['error_code'], 31)

        self.assertIn(
            "phone",
            response.data['detail']
        )

    # ---------------------------------------------------------
    # 12. Duplicate phone number -> error_code 33
    #     (the view's 'قبلاً ثبت' substring check matches the
    #     serializer's Persian duplicate-phone message)
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

        self.assertEqual(response.data['error_code'], 33)

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

    # ---------------------------------------------------------
    # 17. PATCH with an empty body is a no-op
    #     (every field on ProfileUpdateSerializer is
    #     required=False, so sending {} should still return 200
    #     with the profile left completely unchanged)
    # ---------------------------------------------------------

    def test_patch_with_empty_body_is_noop(self):
        response = self.client.patch(
            self.profile_url,
            {},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")
        self.assertEqual(self.user.phone, "09123456789")
        self.assertTrue(self.user.check_password("OldPassword123"))

    # ---------------------------------------------------------
    # 18. username and email are not part of
    #     ProfileUpdateSerializer.Meta.fields, so submitting them
    #     must be silently ignored rather than applied -
    #     this guards against this endpoint being used to bypass
    #     whatever dedicated flow (if any) governs those fields
    # ---------------------------------------------------------

    def test_username_and_email_cannot_be_changed(self):
        data = {
            "username": "hacked_username",
            "email": "hacked@example.com",
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

        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")


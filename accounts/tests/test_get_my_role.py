from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from identity.models import User, Role


class ReturnRoleTest(APITestCase):

    def setUp(self):
        # ================== Create Roles ==================

        self.admin_role = Role.objects.create(
            code='admin',
            title='ادمین',
            level=100,
            is_system=True,
        )

        self.super_admin_role = Role.objects.create(
            code='super_admin',
            title='سوپر ادمین',
            level=999,
            is_system=True,
        )

        self.limited_role = Role.objects.create(
            code='limited',
            title='کاربر محدود شده',
            level=20,
            is_system=True,
        )

        self.regular_role = Role.objects.create(
            code='regular',
            title='کاربر معمولی',
            level=20,
            is_system=True,
        )

        # ================== Create Users ==================

        self.admin_user = User.objects.create_user(
            username='admin_dara',
            password='admin_password123',
            email='admin@test.com',
            phone='09111111111',
            status='active',
            role=self.admin_role
        )

        self.super_admin_user = User.objects.create_user(
            username='super_admin_nima',
            password='super_admin_password123',
            email='superadmin@test.com',
            phone='09222222222',
            status='active',
            role=self.super_admin_role
        )

        self.regular_user = User.objects.create_user(
            username='normal_user',
            password='password123',
            email='normal@test.com',
            phone='09333333333',
            status='active',
            role=self.regular_role
        )

        self.limited_user = User.objects.create_user(
            username='limited_user',
            password='password123',
            email='limited@test.com',
            phone='09555555555',
            status='active',
            role=self.limited_role
        )

        # ================== URL ==================

        self.my_role_url = reverse('my_role')

    # =====================================================
    # Successful Tests
    # =====================================================

    def test_get_my_role_regular_user(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.my_role_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data['username'],
            'normal_user'
        )

        self.assertEqual(
            response.data['role_title'],
            'کاربر معمولی'
        )

    def test_get_my_role_limited_user(self):
        self.client.force_authenticate(user=self.limited_user)

        response = self.client.get(self.my_role_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data['username'],
            'limited_user'
        )

        self.assertEqual(
            response.data['role_title'],
            'کاربر محدود شده'
        )

    def test_get_my_role_admin_user(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.my_role_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data['username'],
            'admin_dara'
        )

        self.assertEqual(
            response.data['role_title'],
            'ادمین'
        )

    def test_get_my_role_super_admin_user(self):
        self.client.force_authenticate(user=self.super_admin_user)

        response = self.client.get(self.my_role_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data['username'],
            'super_admin_nima'
        )

        self.assertEqual(
            response.data['role_title'],
            'سوپر ادمین'
        )

    # =====================================================
    # User Without Role
    # =====================================================

    def test_get_my_role_user_without_role(self):
        user = User.objects.create_user(
            username='no_role_user',
            password='password123',
            email='norole@test.com',
            phone='09666666666',
            status='active',
            role=None
        )

        self.client.force_authenticate(user=user)

        response = self.client.get(self.my_role_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data['username'],
            'no_role_user'
        )

    # =====================================================
    # Authentication Tests
    # =====================================================

    def test_get_my_role_unauthenticated(self):
        response = self.client.get(self.my_role_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    # =====================================================
    # Error Handling
    # =====================================================

    @patch(
        'accounts.views.get_my_role.ReturnRoleUsersSerializer'
    )
    def test_get_my_role_serializer_error(
        self,
        mock_serializer
    ):
        self.client.force_authenticate(user=self.admin_user)

        mock_serializer.side_effect = Exception(
            'Serializer error'
        )

        response = self.client.get(self.my_role_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        self.assertIn(
            'detail',
            response.data
        )

        self.assertEqual(
            response.data['detail'],
            'An error occurred while fetching user role / '
            'خطایی در دریافت نقش کاربر رخ داده است.'
        )


from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, Role

class AdminUserManagmentTest(APITestCase):
    def setUp(self):
        # create roles
        self.admin_role = Role.objects.create(
            code='admin',
            title='ادمین',
            level = 100 ,
            is_system = True,
        )

        self.super_admin_role = Role.objects.create(
            code='super_admin',
            title='سوپر ادمین',
            level = 999 ,
            is_system = True,
        )

        self.regular_role = Role.objects.create(
            code='limited',
            title='کاربر محدود شده ',
            level = 20 ,
            is_system = True,
        )

        self.limited_role = Role.objects.create(
            code='regular',
            title='کاربر معمولی',
            level = 20 ,
            is_system = True,
        )
        # create_user
        self.admin_user = User.objects.create(
            username="admin_dara",
            password="admin_password123",
            email="admin@test.com",
            phone="+989111111111",
            status="active",
            role=self.admin_role
        )
        self.super_admin_user = User.objects.create(
            username="super_admin_nima",
            password="super_admin_password123",
            email="superadmin@test.com",
            phone="+989222222222",
            status="active",
            role=self.super_admin_role
        )
        self.regular_user = User.objects.create_user(
            username="normal_user",
            password="password123",
            email="normal@test.com",
            phone="+989333333333",
            status="active",
            role=self.regular_role
        )
        self.target_user = User.objects.create_user(
            username="pending_user",
            password="password123",
            email="target@test.com",
            phone="+989444444444",
            status="pending"
        )
        # define urls
        self.list_users_url = reverse('list-of-users')
        self.pending_users_url = reverse('pending-users')
        self.list_roles_url = reverse('list-of-roles')

        self.assign_role_url = lambda pk: reverse('assign-users-role', kwargs={'pk': pk})
        self.manage_status_url = lambda pk: reverse('manage-user-status', kwargs={'pk': pk})
        self.activation_url = lambda pk: reverse('is-active', kwargs={'pk': pk})

    def test_regular_user_cannot_access_admin_endpoints(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.pending_users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        data = {'status': 'active'}
        response = self.client.patch(self.manage_status_url(self.target_user.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_get_lists(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.list_users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 4)

        response = self.client.get(self.pending_users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.list_roles_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 4)

    def test_assign_user_role_success(self):
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'role': self.super_admin_role.id
        }
        response = self.client.patch(self.assign_role_url(self.target_user.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.role, self.super_admin_role)

    def test_assign_user_role_unsuccess(self):
        self.client.force_authenticate(user=self.admin_user)

        first_data = {
            'role': self.super_admin_role.id
        }
        response = self.client.patch(self.assign_role_url(999), first_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error_code'],40)

        invalid_data = {'role': 999}
        response = self.client.patch(self.assign_role_url(self.target_user.pk), invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)

    def test_manage_user_status_success(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'status': 'suspended'
        }
        response = self.client.patch(self.manage_status_url(self.target_user.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.status, 'suspended')

    def test_manage_user_status_unsuccess_code_10(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'status': 'close'
        }
        response = self.client.patch(self.manage_status_url(self.target_user.pk), data, format='json')
        self.assertEqual(response.data['error_code'],10)

    def test_manage_user_status_unsuccess_code_40(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'status': 'suspended'
        }
        response = self.client.patch(self.manage_status_url(999), data, format='json')
        self.assertEqual(response.data['error_code'],40)

    def test_soft_delete_user_success(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.manage_status_url(self.target_user.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.status, 'deleted')
        self.assertIsNotNone(self.target_user.deleted_at)

    def test_user_activation_patch_success(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'is_active': False
        }
        response = self.client.patch(self.activation_url(self.target_user.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

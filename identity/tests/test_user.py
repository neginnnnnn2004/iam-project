from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from identity.models import User, Role

class AdminUserManagementTest(APITestCase):

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

        self.limited_role= Role.objects.create(
            code='limited',
            title='کاربر محدود شده ',
            level = 20 ,
            is_system = True,
        )

        self.regular_role = Role.objects.create(
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
            phone="09111111111",
            status="active",
            role=self.admin_role
        )
        self.super_admin_user = User.objects.create(
            username="super_admin_nima",
            password="super_admin_password123",
            email="superadmin@test.com",
            phone="09222222222",
            status="active",
            role=self.super_admin_role
        )
        self.regular_user = User.objects.create_user(
            username="normal_user",
            password="password123",
            email="normal@test.com",
            phone="09333333333",
            status="unverified",
            role=self.regular_role
        )
        self.target_user = User.objects.create_user(
            username="pending_user",
            password="password123",
            email="target@test.com",
            phone="09444444444",
            status="pending"
        )
        self.limited_user = User.objects.create_user(
            username="limited_user",
            password="password123",
            email="limited@test.com",
            phone="09555555555",
            status="active",
            role=self.limited_role
        )

        # define urls
        self.list_users_url = reverse('list-of-users')
        self.pending_users_url = reverse('pending-users')
        self.list_roles_url = reverse('list-of-roles')
        self.my_role_url=reverse('my_role')

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

    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.list_users_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(len(response.data), 5)

    def test_admin_can_list_pending_users(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.pending_users_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(len(response.data), 1)

    def test_admin_can_list_roles(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.list_roles_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(len(response.data), 4)

    #######################
    def test_regular_user_can_not_list_users(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.list_users_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_limited_user_can_not_list_users(self):
        self.client.force_authenticate(user=self.limited_user)

        response = self.client.get(self.list_users_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_regular_user_can_not_list_roles(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.list_roles_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_limited_user_can_not_list_roles(self):
        self.client.force_authenticate(user=self.limited_user)

        response = self.client.get(self.list_roles_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_regular_user_can_not_list_pending_users(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.pending_users_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_limited_user_can_not_list_pending_users(self):
        self.client.force_authenticate(user=self.limited_user)

        response = self.client.get(self.pending_users_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )
#############
    def test_Unauthenticated_user_can_not_list_pending_users(self):
        response = self.client.get(self.list_users_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
    def test_Unauthenticated_user_can_not_list_users(self):
        response = self.client.get(self.list_users_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
    def test_Unauthenticated_user_can_not_list_roles(self):
        response = self.client.get(self.list_users_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
 #########################

    def test_get_my_role(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.my_role_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_assign_role_to_user_success(self):
        self.client.force_authenticate(user=self.super_admin_user)
        data = {
            'role': self.regular_role.id
        }
        response = self.client.patch(self.assign_role_url(self.target_user.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    def test_assign_role_to_user_unsuccess(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'role': self.regular_role.id
        }
        response = self.client.patch(self.assign_role_url(self.target_user.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    def test_assign_role_to_user_unsuccess2(self):
        data = {
            'role': self.regular_role.id
        }
        response = self.client.patch(self.assign_role_url(self.target_user.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    #########################
    # Manage User Status
    #########################

    def test_super_admin_can_change_user_status(self):
        self.client.force_authenticate(user=self.super_admin_user)

        data = {
            'status': 'active'
        }

        response = self.client.patch(
            self.manage_status_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.target_user.refresh_from_db()

        self.assertEqual(
            self.target_user.status,
            'active'
        )

    def test_admin_can_not_change_user_status(self):
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'status': 'active'
        }

        response = self.client.patch(
            self.manage_status_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_regular_user_can_not_change_user_status(self):
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'status': 'active'
        }

        response = self.client.patch(
            self.manage_status_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_unauthenticated_user_can_not_change_user_status(self):
        data = {
            'status': 'active'
        }

        response = self.client.patch(
            self.manage_status_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_super_admin_can_not_change_status_with_invalid_value(self):
        self.client.force_authenticate(user=self.super_admin_user)

        data = {
            'status': 'invalid_status'
        }

        response = self.client.patch(
            self.manage_status_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_change_status_for_non_existing_user(self):
        self.client.force_authenticate(user=self.super_admin_user)

        data = {
            'status': 'active'
        }

        response = self.client.patch(
            self.manage_status_url(99999),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    #########################
    # Soft Delete User
    #########################

    def test_super_admin_can_soft_delete_user(self):
        self.client.force_authenticate(user=self.super_admin_user)

        response = self.client.delete(
            self.manage_status_url(self.target_user.pk)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.target_user.refresh_from_db()

        self.assertIsNotNone(
            self.target_user.deleted_at
        )

        self.assertEqual(
            self.target_user.status,
            'deleted'
        )

    def test_admin_can_not_soft_delete_user(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(
            self.manage_status_url(self.target_user.pk)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_regular_user_can_not_soft_delete_user(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.delete(
            self.manage_status_url(self.target_user.pk)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_unauthenticated_user_can_not_soft_delete_user(self):
        response = self.client.delete(
            self.manage_status_url(self.target_user.pk)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_soft_delete_non_existing_user(self):
        self.client.force_authenticate(user=self.super_admin_user)

        response = self.client.delete(
            self.manage_status_url(99999)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    #########################
    # User Activation
    #########################

    def test_admin_can_activate_user(self):
        self.client.force_authenticate(user=self.admin_user)

        self.target_user.is_active = False
        self.target_user.save()

        data = {
            'is_active': True
        }

        response = self.client.patch(
            self.activation_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.target_user.refresh_from_db()

        self.assertTrue(
            self.target_user.is_active
        )

    def test_admin_can_deactivate_user(self):
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'is_active': False
        }

        response = self.client.patch(
            self.activation_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.target_user.refresh_from_db()

        self.assertFalse(
            self.target_user.is_active
        )

    def test_super_admin_can_activate_user(self):
        self.client.force_authenticate(user=self.super_admin_user)

        self.target_user.is_active = False
        self.target_user.save()

        data = {
            'is_active': True
        }

        response = self.client.patch(
            self.activation_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_regular_user_can_not_activate_user(self):
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'is_active': True
        }

        response = self.client.patch(
            self.activation_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_limited_user_can_not_activate_user(self):
        self.client.force_authenticate(user=self.limited_user)

        data = {
            'is_active': True
        }

        response = self.client.patch(
            self.activation_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_unauthenticated_user_can_not_activate_user(self):
        data = {
            'is_active': True
        }

        response = self.client.patch(
            self.activation_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_activate_non_existing_user(self):
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'is_active': True
        }

        response = self.client.patch(
            self.activation_url(99999),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_activate_user_with_invalid_payload(self):
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'is_active': 'invalid'
        }

        response = self.client.patch(
            self.activation_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_activate_soft_deleted_user(self):
        self.client.force_authenticate(user=self.admin_user)

        self.target_user.deleted_at = timezone.now()
        self.target_user.save()

        data = {
            'is_active': True
        }

        response = self.client.patch(
            self.activation_url(self.target_user.pk),
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User, Role
from django.urls import reverse

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
#########################
# Manage User Status
#########################

    def test_super_admin_can_change_user_status(self):
        self.client.force_authenticate(user=self.super_admin_user)
        url = reverse('manage-user-status', kwargs={'pk': self.target_user.pk})
        data = {'status': 'active'}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.target_user.refresh_from_db()

        self.assertEqual(self.target_user.status,'active')


    def test_admin_can_not_change_user_status(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('manage-user-status', kwargs={'pk': self.target_user.pk})
        data = {'status': 'active'}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_regular_user_can_not_change_user_status(self):
        self.client.force_authenticate(user=self.regular_user)

        url = reverse('manage-user-status', kwargs={'pk': self.target_user.pk})
        data = {'status': 'active'}


        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_unauthenticated_user_can_not_change_user_status(self):

        url = reverse('manage-user-status', kwargs={'pk': self.target_user.pk})
        data = {'status': 'active'}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_super_admin_can_not_change_status_with_invalid_value(self):
        self.client.force_authenticate(user=self.super_admin_user)

        url = reverse('manage-user-status', kwargs={'pk': self.target_user.pk})
        data = {'status': 'invalid_status'}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_change_status_for_non_existing_user(self):
        self.client.force_authenticate(user=self.super_admin_user)

        url = reverse('manage-user-status', kwargs={'pk': 9999})
        data = {'status': 'active'}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    #########################
    # Soft Delete User
    #########################

    def test_super_admin_can_soft_delete_user(self):
        self.client.force_authenticate(user=self.super_admin_user)

        url = reverse('manage-user-status', kwargs={'pk': self.target_user.pk})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


        self.target_user.refresh_from_db()

        self.assertIsNotNone(self.target_user.deleted_at)

        self.assertEqual(self.target_user.status,'deleted')


    def test_admin_can_not_soft_delete_user(self):
        self.client.force_authenticate(user=self.admin_user)

        url = reverse('manage-user-status', kwargs={'pk': self.target_user.pk})

        response = self.client.patch(url, format='json')
        self.assertEqual(response.status_code,status.HTTP_403_FORBIDDEN)


    def test_regular_user_can_not_soft_delete_user(self):
        self.client.force_authenticate(user=self.regular_user)

        url = reverse('manage-user-status', kwargs={'pk': self.target_user.pk})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code,status.HTTP_403_FORBIDDEN)


    def test_unauthenticated_user_can_not_soft_delete_user(self):
        url = reverse('manage-user-status', kwargs={'pk': self.target_user.pk})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)


    def test_soft_delete_non_existing_user(self):
        self.client.force_authenticate(user=self.super_admin_user)

        url = reverse('manage-user-status', kwargs={'pk': 9999})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)

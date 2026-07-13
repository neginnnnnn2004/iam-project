from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, Role, Group, UserGroup

class GroupUserManagmentTest(APITestCase):
    def setUp(self):
        # create_roles
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
            code='regular',
            title='کاربر معمولی',
            level=20,
            is_system=True,
        )
        # create_user
        self.admin_user = User.objects.create_user(
            username="admin_dara",
            password="admin_password123",
            email="admin@test.com",
            phone="+989111111111",
            status="active",
            role=self.admin_role
        )
        self.super_admin_user = User.objects.create_user(
            username="super_admin_nima",
            password="super_admin_password123",
            email="superadmin@test.com",
            phone="+989222222222",
            status="active",
            role=self.super_admin_role
        )
        self.target_user = User.objects.create_user(
            username="user_83",
            password="password123",
            email="target@test.com",
            phone="+989444444444",
            status="pending"
        )
        # create_group
        self.sample_group = Group.objects.create(
            title="development team",
            description="System programmers group",
            assigned_by=self.super_admin_user
        )
        # define urls
        self.list_groups_url = reverse('list-of-groups')
        self.group_register_url = reverse('group-register')
        self.group_detail_url = lambda pk: reverse('group_detail', kwargs={'pk': pk})
        self.assign_user_to_group_url = reverse('assign-users-group')

    def test_regular_user_cannot_access_admin_endpoints(self):
        self.client.force_authenticate(user=self.target_user)

        response = self.client.get(self.list_groups_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.group_register_url, {'title': 'new group'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_get_list_groups_success(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_groups_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_create_group_success(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'title': 'frontend team',
            'description': 'Frontend programmers group'
        }
        response = self.client.post(self.group_register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data['title'], 'frontend team')

        created_group = Group.objects.get(title='frontend team')
        self.assertEqual(created_group.title_normalized, 'frontend team')

    def test_create_group_unsuccess_code_10(self):
        self.client.force_authenticate(user=self.super_admin_user)
        data = {
            'title': '',
            'description': 'without title'
        }
        response = self.client.post(self.group_register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)

    def test_get_group_detail_success(self):
        self.client.force_authenticate(user=self.super_admin_user)
        response = self.client.get(self.group_detail_url(self.sample_group.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.sample_group.title)

    def test_get_group_detail_not_found_code_50(self):
        self.client.force_authenticate(user=self.super_admin_user)
        response = self.client.get(self.group_detail_url(999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error_code'], 50)

    def test_update_group_full_success(self):
        self.client.force_authenticate(user=self.super_admin_user)
        data = {
            'title': 'backend team',
            'description': 'Backend programmers group'
        }
        response = self.client.put(self.group_detail_url(self.sample_group.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.sample_group.refresh_from_db()
        self.assertEqual(self.sample_group.title, 'backend team')

    def test_update_group_partial_success(self):
        self.client.force_authenticate(user=self.super_admin_user)
        data = {
            'description': 'Back_end programmers group'
        }
        response = self.client.patch(self.group_detail_url(self.sample_group.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.sample_group.refresh_from_db()
        self.assertEqual(self.sample_group.description, 'Back_end programmers group')

    def test_soft_delete_group_success(self):
        self.client.force_authenticate(user=self.super_admin_user)

        response = self.client.delete(self.group_detail_url(self.sample_group.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.sample_group.refresh_from_db()
        self.assertIsNotNone(self.sample_group.deleted_at)

    def test_assign_user_to_group_success(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'user': self.target_user.id,
            'group': self.sample_group.id,
            'is_primary': True
        }
        response = self.client.post(self.assign_user_to_group_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        membership_exists = UserGroup.objects.filter(
            user=self.target_user,
            group=self.sample_group,
            assigned_by=self.admin_user
        ).exists()
        self.assertTrue(membership_exists)

    def test_assign_user_to_group_unsuccess_code_10(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'user': 4000,
            'group': self.sample_group.id
        }
        response = self.client.post(self.assign_user_to_group_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)
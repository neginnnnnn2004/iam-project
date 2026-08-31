from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User, Role, Group, UserGroup

class GroupListTest(APITestCase):
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

        # create_group
        self.group_one= Group.objects.create(
            title = "backend",
            description = "this is for backend developers",
        )
        self.group_two = Group.objects.create(
            title = "general",
            description = "this is a general group",
        )
        self.group_three = Group.objects.create(
            title = "finance",
            description = "this is for finance developers",
        )

        # create_user_group
        # self.active_regular_user_group_list
        UserGroup.objects.create(
            user = self.regular_user,
            group =  self.group_one,
            is_primary = False
        )
        # self.active_limited_user_group_list
        UserGroup.objects.create(
            user = self.limited_user,
            group =  self.group_three,
            is_primary = True
        )
        # self.pending_user_cant_list_group
        UserGroup.objects.create(
            user = self.target_user,
            group =  self.group_two,
            is_primary = True
        )


        # define urls
        self.register_group_url = reverse('group-register')

    def test_successful_register1(self):
        self.client.force_authenticate(user=self.admin_user)
        valid_data1 = {
            'title': 'UiUx',
            'description': 'this is for UiUx developers',
        }

        response = self.client.post(
            self.register_group_url,
            valid_data1,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        valid_data2 = {
            'title': 'test',
            'description': 'this is for test developers',
        }

        response = self.client.post(
            self.register_group_url,
            valid_data2,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_successful_register2(self):
        self.client.force_authenticate(user=self.super_admin_user)
        valid_data1 = {
            'title': 'UiUx',
            'description': 'this is for UiUx developers',
        }

        response = self.client.post(
            self.register_group_url,
            valid_data1,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        valid_data2 = {
            'title': 'test',
            'description': 'this is for test developers',
        }

        response = self.client.post(
            self.register_group_url,
            valid_data2,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_regular_user_cant_register_group(self):
        self.client.force_authenticate(user=self.regular_user)
        valid_data1 = {
            'title': 'UiUx',
            'description': 'this is for UiUx developers',
        }

        response = self.client.post(
            self.register_group_url,
            valid_data1,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_limited_user_cant_register_group(self):
        self.client.force_authenticate(user=self.limited_user)
        valid_data1 = {
            'title': 'UiUx',
            'description': 'this is for UiUx developers',
        }

        response = self.client.post(
            self.register_group_url,
            valid_data1,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_unauthenticated_user_cant_register_group(self):
        valid_data1 = {
            'title': 'UiUx',
            'description': 'this is for UiUx developers',
        }

        response = self.client.post(
            self.register_group_url,
            valid_data1,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_unsuccessful_register(self):
        self.client.force_authenticate(user=self.admin_user),

        valid_data1 = {
            'title': '',
            'description': 'this is for UiUx developers',
        }

        response = self.client.post(
            self.register_group_url,
            valid_data1,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User, Role

class ReturnRoleTest(APITestCase):

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
        self.admin_user = User.objects.create_user(
            username="admin_dara",
            password="admin_password123",
            email="admin@test.com",
            phone="09111111111",
            status="active",
            role=self.admin_role
        )
        self.super_admin_user = User.objects.create_user(
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

        # define url
        self.my_role_url=reverse('my_role')

    def test_get_my_role_success1(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.my_role_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_get_my_role_success2(self):
        self.client.force_authenticate(user=self.limited_user)

        response = self.client.get(self.my_role_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_get_my_role_success3(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.my_role_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_get_my_role_success4(self):
        self.client.force_authenticate(user=self.super_admin_user)

        response = self.client.get(self.my_role_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_get_my_role_unsuccess(self):

        response = self.client.get(self.my_role_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
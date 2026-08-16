from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User, Role, Group, UserGroup


class GroupDetailTest(APITestCase):
    def setUp(self):
        # ===== Roles =====
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

        # ===== Users =====
        self.admin_user = User.objects.create(
            username="admin_dara",
            password="admin_password123",
            email="admin@test.com",
            phone="09111111111",
            status="active",
            role=self.admin_role,
        )
        self.super_admin_user = User.objects.create(
            username="super_admin_nima",
            password="super_admin_password123",
            email="superadmin@test.com",
            phone="09222222222",
            status="active",
            role=self.super_admin_role,
        )
        self.regular_user = User.objects.create_user(
            username="normal_user",
            password="password123",
            email="normal@test.com",
            phone="09333333333",
            status="unverified",
            role=self.regular_role,
        )
        self.target_user = User.objects.create_user(
            username="pending_user",
            password="password123",
            email="target@test.com",
            phone="09444444444",
            status="pending",
        )
        self.limited_user = User.objects.create_user(
            username="limited_user",
            password="password123",
            email="limited@test.com",
            phone="09555555555",
            status="active",
            role=self.limited_role,
        )

        # ===== Groups =====
        self.group_one = Group.objects.create(
            title="backend",
            description="this is for backend developers",
        )
        self.group_two = Group.objects.create(
            title="general",
            description="this is a general group",
        )
        self.group_three = Group.objects.create(
            title="finance",
            description="this is for finance developers",
        )

        # گروه حذف‌شده (soft delete)
        self.group_five = Group.objects.create(
            title="deleted_group",
            description="this group will be deleted",
        )
        self.deleted_group_id = self.group_five.id
        self.group_five.deleted_at = timezone.now()
        self.group_five.save()

        # # ===== UserGroups =====
        # UserGroup.objects.create(
        #     user=self.regular_user,
        #     group=self.group_one,
        #     is_primary=False,
        # )
        # UserGroup.objects.create(
        #     user=self.limited_user,
        #     group=self.group_three,
        #     is_primary=True,
        # )
        # UserGroup.objects.create(
        #     user=self.target_user,
        #     group=self.group_two,
        #     is_primary=True,
        # )

    # ============================================================
    #  POST — انتساب نقش
    # ============================================================

    def test_unauthenticated_user_gets_401(self):
        """کاربر بدون احراز هویت → 401"""
        url = reverse('assign-users-group')
        valid_data = {
            'group' : self.group_one.id,
            'user' : self.regular_user.id,
            'is_primary' : True,
        }
        response = self.client.post(url,valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cant_assign_user_group(self):
        """کاربر عادی → 403"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('assign-users-group')
        valid_data = {
            'group' : self.group_one.id,
            'user' : self.regular_user.id,
            'is_primary' : True,
        }
        response = self.client.post(url,valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_limited_user_cant_assign_user_group(self):
        """کاربر محدود → 403"""
        self.client.force_authenticate(user=self.limited_user)
        url = reverse('assign-users-group')
        valid_data = {
            'group' : self.group_one.id,
            'user' : self.regular_user.id,
            'is_primary' : True,
        }
        response = self.client.post(url,valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_can_assign_user_group(self):
        self.client.force_authenticate(user=self.admin_user)
        """ادمین → 200 و دیتای صحیح"""
        url = reverse('assign-users-group')
        valid_data = {
            'group' : self.group_one.id,
            'user' : self.regular_user.id,
            'is_primary' : True,
        }
        response = self.client.post(url,valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_super_admin_user_can_assign_user_group(self):
        self.client.force_authenticate(user=self.super_admin_user)
        """سوپر ادمین → 200 و دیتای صحیح"""
        url = reverse('assign-users-group')
        valid_data = {
            'group' : self.group_two.id,
            'user' : self.limited_user.id,
            'is_primary' : True,
        }
        response = self.client.post(url,valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_super_admin_user_can_assign_user_group_error_10_not_found_group(self):
        self.client.force_authenticate(user=self.super_admin_user)
        url = reverse('assign-users-group')
        valid_data = {
            'group' : 999,
            'user' : self.limited_user.id,
            'is_primary' : True,
        }
        response = self.client.post(url,valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_super_admin_user_can_assign_user_group_error_10_not_found_user(self):
        self.client.force_authenticate(user=self.super_admin_user)
        url = reverse('assign-users-group')
        valid_data = {
            'group' : self.group_two.id,
            'user' : 888,
            'is_primary' : True,
        }
        response = self.client.post(url,valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_super_admin_user_can_assign_user_group_error_10_wrong_type_primary(self):
        self.client.force_authenticate(user=self.super_admin_user)
        url = reverse('assign-users-group')
        valid_data = {
            'group' : 999,
            'user' : self.limited_user.id,
            'is_primary' : "True",
        }
        response = self.client.post(url,valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
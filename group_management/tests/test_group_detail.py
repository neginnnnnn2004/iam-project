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

        # ===== UserGroups =====
        UserGroup.objects.create(
            user=self.regular_user,
            group=self.group_one,
            is_primary=False,
        )
        UserGroup.objects.create(
            user=self.limited_user,
            group=self.group_three,
            is_primary=True,
        )
        UserGroup.objects.create(
            user=self.target_user,
            group=self.group_two,
            is_primary=True,
        )

    # ============================================================
    #  GET — دسترسی‌ها
    # ============================================================

    def test_unauthenticated_user_gets_401(self):
        """کاربر بدون احراز هویت → 401"""
        url = reverse('group-detail', args=[self.group_one.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cant_see_group_detail(self):
        """کاربر عادی → 403"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('group-detail', args=[self.group_one.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_limited_user_cant_see_group_detail(self):
        """کاربر محدود → 403"""
        self.client.force_authenticate(user=self.limited_user)
        url = reverse('group-detail', args=[self.group_three.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_sees_group_detail(self):
        """ادمین → 200 و دیتای صحیح"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('group-detail', args=[self.group_three.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('finance', response.data['title'])

    def test_super_admin_sees_group_detail(self):
        """سوپر ادمین → 200 و دیتای صحیح"""
        self.client.force_authenticate(user=self.super_admin_user)
        url = reverse('group-detail', args=[self.group_two.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('general', response.data['title'])

    def test_get_deleted_group_returns_404(self):
        """گروه حذف‌شده → 404 (کد 50)"""
        self.client.force_authenticate(user=self.super_admin_user)
        url = reverse('group-detail', args=[self.deleted_group_id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error_code'], 50)

    def test_get_nonexistent_group_returns_404(self):
        """گروه ناموجود → 404 (کد 50)"""
        self.client.force_authenticate(user=self.super_admin_user)
        url = reverse('group-detail', args=[999])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error_code'], 50)

    # ============================================================
    #  PATCH — ویرایش
    # ============================================================

    def test_admin_can_update_group(self):
        """ادمین می‌تونه گروه رو ویرایش کنه → 200"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('group-detail', args=[self.group_one.id])
        valid_data = {"title": "backend_v2"}
        response = self.client.patch(url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'backend_v2')

    def test_update_invalid_data_returns_400(self):
        """داده نامعتبر → 400 (کد 10)"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('group-detail', args=[self.group_one.id])
        invalid_data = {"title": ""}  # فرضاً title نمی‌تونه خالی باشه
        response = self.client.patch(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 10)

    def test_update_deleted_group_returns_404(self):
        """ویرایش گروه حذف‌شده → 404"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('group-detail', args=[self.deleted_group_id])
        response = self.client.patch(url, {"title": "x"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_regular_user_cant_update_group(self):
        """کاربر عادی نمی‌تونه ویرایش کنه → 403"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('group-detail', args=[self.group_one.id])
        response = self.client.patch(url, {"title": "x"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ============================================================
    #  DELETE — حذف منطقی
    # ============================================================

    def test_admin_can_delete_group(self):
        """ادمین می‌تونه گروه رو حذف کنه → 204"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('group-detail', args=[self.group_one.id])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # بررسی اینکه واقعاً soft delete شده
        self.group_one.refresh_from_db()
        self.assertIsNotNone(self.group_one.deleted_at)

    def test_delete_already_deleted_group_returns_404(self):
        """حذف گروهی که قبلاً حذف شده → 404"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('group-detail', args=[self.deleted_group_id])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_group_returns_404(self):
        """حذف گروه ناموجود → 404"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('group-detail', args=[999])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_regular_user_cant_delete_group(self):
        """کاربر عادی نمی‌تونه حذف کنه → 403"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('group-detail', args=[self.group_one.id])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

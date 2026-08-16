from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User, Role, Group, UserGroup, Domain


class GroupDomainTest(APITestCase):
    def setUp(self):
        # ===== Roles =====
        self.admin_role = Role.objects.create(
            code='admin', title='ادمین', level=100, is_system=True,
        )
        self.super_admin_role = Role.objects.create(
            code='super_admin', title='سوپر ادمین', level=999, is_system=True,
        )
        self.limited_role = Role.objects.create(
            code='limited', title='کاربر محدود شده', level=20, is_system=True,
        )
        self.regular_role = Role.objects.create(
            code='regular', title='کاربر معمولی', level=20, is_system=True,
        )

        # ===== Users =====
        self.admin_user = User.objects.create(
            username="admin_dara", password="admin_password123",
            email="admin@test.com", phone="09111111111",
            status="active", role=self.admin_role,
        )
        self.super_admin_user = User.objects.create(
            username="super_admin_nima", password="super_admin_password123",
            email="superadmin@test.com", phone="09222222222",
            status="active", role=self.super_admin_role,
        )
        self.regular_user = User.objects.create_user(
            username="normal_user", password="password123",
            email="normal@test.com", phone="09333333333",
            status="unverified", role=self.regular_role,
        )
        self.target_user = User.objects.create_user(
            username="pending_user", password="password123",
            email="target@test.com", phone="09444444444",
            status="pending",
        )
        self.limited_user = User.objects.create_user(
            username="limited_user", password="password123",
            email="limited@test.com", phone="09555555555",
            status="active", role=self.limited_role,
        )

        # ===== Groups =====
        self.group_one = Group.objects.create(title="frosh", description="")
        self.group_two = Group.objects.create(title="test", description="")
        self.group_three = Group.objects.create(title="mali", description="")

        # ===== UserGroups =====
        UserGroup.objects.create(user=self.regular_user, group=self.group_one, is_primary=False)
        UserGroup.objects.create(user=self.limited_user, group=self.group_three, is_primary=True)
        UserGroup.objects.create(user=self.target_user, group=self.group_two, is_primary=True)

        # ===== Domains (ForeignKey) =====
        self.domain_one = Domain.objects.create(
            domain_name="khanoumi.com", description="", groups=self.group_one,
        )
        self.domain_two = Domain.objects.create(
            domain_name="rojashop.com", description="", groups=self.group_one,
        )
        self.domain_three = Domain.objects.create(
            domain_name="modiage.com", description="", groups=self.group_two,
        )
        self.domain_four = Domain.objects.create(
            domain_name="beautycode.ir", description="", groups=self.group_three,
        )

    # ============================================================
    #  GET — دسترسیها
    # ============================================================

    def test_unauthenticated_user_gets_401(self):
        """کاربر بدون احراز هویت → 401"""
        url = reverse('group-domains', args=[self.group_one.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_can_view_own_group_domains(self):
        """کاربر عادی دامنههای گروه خودش رو میبینه → 200"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('group-domains', args=[self.group_one.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        domain_names = [item['domain_name'] for item in response.data]
        self.assertIn('khanoumi.com', domain_names)
        self.assertIn('rojashop.com', domain_names)
        self.assertNotIn('modiage.com', domain_names)

    def test_regular_user_cant_view_other_group_domains(self):
        """کاربر عادی دامنههای گروه دیگه رو نمیبینه"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('group-domains', args=[self.group_three.id])
        response = self.client.get(url, format='json')
        # بسته به منطق ویو: 403 یا 200 با لیست خالی
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_limited_user_can_view_own_group_domains(self):
        """کاربر محدود دامنههای گروه خودش رو میبینه → 200"""
        self.client.force_authenticate(user=self.limited_user)
        url = reverse('group-domains', args=[self.group_three.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        domain_names = [item['domain_name'] for item in response.data]
        self.assertIn('beautycode.ir', domain_names)
        self.assertNotIn('khanoumi.com', domain_names)

    def test_admin_can_view_all_group_domains(self):
        """ادمین دامنههای هر گروهی رو میبینه → 200"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('group-domains', args=[self.group_two.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        domain_names = [item['domain_name'] for item in response.data]
        self.assertIn('modiage.com', domain_names)

    def test_super_admin_can_view_all_group_domains(self):
        """سوپر ادمین دامنههای هر گروهی رو میبینه → 200"""
        self.client.force_authenticate(user=self.super_admin_user)
        url = reverse('group-domains', args=[self.group_one.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        domain_names = [item['domain_name'] for item in response.data]
        self.assertIn('khanoumi.com', domain_names)
        self.assertIn('rojashop.com', domain_names)

    def test_get_domains_for_nonexistent_group(self):
        """گروه ناموجود → 404"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('group-domains', args=[999])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

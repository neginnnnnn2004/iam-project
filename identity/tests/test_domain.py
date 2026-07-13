from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from identity.models import User, Role, Group, UserGroup, Domain, Tag, User_Domain_Tag

class DomainTest(APITestCase):
    def setUp(self):
        #create role
        self.admin_role = Role.objects.create(
            code='admin',
            title='ادمین',
            level=100,
            is_system=True
        )
        self.regular_role = Role.objects.create(
            code='regular',
            title='کاربر معمولی',
            level=20,
            is_system=True,
        )
        #create user
        self.admin_user = User.objects.create_user(
            username="admin_dara",
            password="admin_password123",
            email="admin@test.com",
            phone="+989111111111",
            status="active",
            role=self.admin_role
        )
        self.regular_user = User.objects.create_user(
            username="user_normal",
            password="password123",
            email="user@test.com",
            phone="+989333333333",
            status="active",
            role=self.regular_role
        )
        self.user_wo_no_group = User.objects.create_user(
            username="user83",
            password="password123",
            email="user83@test.com",
            phone="+989999999999",
            status="active",
            role=self.regular_role
        )
        #create group
        self.sample_group = Group.objects.create(
            title="technical team",
            description="Programmer group",
            assigned_by=self.admin_user
        )
        #user group
        UserGroup.objects.create(
            user=self.regular_user,
            group=self.sample_group,
            assigned_by=self.admin_user
        )
        #import domains:
        self.grouped_domain = Domain.objects.create(
            domain_name="google.com",
        )

        self.grouped_domain.group_id.set([self.sample_group])

        self.public_domain = Domain.objects.create(
            domain_name="github.com",
        )
        #create tags:
        self.sample_tag_1 = Tag.objects.create(
            tag_title="PenetrationTesting",
            created_by=self.admin_user
        )
        self.sample_tag_2 = Tag.objects.create(
            tag_title="HighSecurity",
            created_by=self.admin_user
        )
        #assign a tag to domain
        self.existing_relation = User_Domain_Tag.objects.create(
            user=self.regular_user,
            domain=self.grouped_domain,
            tag=self.sample_tag_1,
        )
        #define url
        self.domain_register_url = reverse('domain-register')
        self.list_of_domains_url = reverse('list-of-domains')
        self.tag_register_url = reverse('tag-register')
        self.list_of_tags_url = reverse('list-of-tags')
        self.assign_tag_url = reverse('assign-a-tag')

    def test_not_allowed_import_domain(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(self.domain_register_url,{'title':'new domain'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_Unauthorized_import_domain(self):

        response = self.client.post(self.domain_register_url,{'title':'new domain'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bad_req_import_domain(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'domain_name': '',
            'group_id': self.sample_group.id,
        }
        response = self.client.post(self.domain_register_url,data,format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)

    def test_import_domain_success(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'domain_name': 'microsoft.com',
            'group_id': [self.sample_group.id],
        }
        response = self.client.post(self.domain_register_url,data,format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['domain_name'], 'microsoft.com')
####################################################################################################
    def test_Unauthorized_get_list_of_domains(self):

        response = self.client.get(self.list_of_domains_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_get_list_domains_success1(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.list_of_domains_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_get_list_domains_success2(self):
        self.client.force_authenticate(user=self.user_wo_no_group)

        response = self.client.get(self.list_of_domains_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_get_list_domains_success3(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.list_of_domains_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
####################################################################################################
    def test_not_allowed_create_tag(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(self.tag_register_url,{'tag_title':'fake'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_Unauthorized_create_tag(self):

        response = self.client.post(self.tag_register_url,{'tag_title':'fake'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bad_req_create_tag(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'tag_title': ''
        }
        response = self.client.post(self.tag_register_url,data,format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)

    def test_create_tag_success(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'tag_title': 'fake'
        }
        response = self.client.post(self.tag_register_url,data,format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tag_title'], 'fake')
####################################################################################################
    def test_Unauthorized_get_list_of_tags(self):

        response = self.client.get(self.list_of_tags_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_list_of_all_tags_success(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.list_of_tags_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
####################################################################################################
#post method tests#
    def test_Unauthorized_for_assign_tag_to_domain(self):

        response = self.client.get(self.assign_tag_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bad_req_for_assign_tag_to_domain(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'domain_name': 'github.com',
            'tag_title': ''
        }

        response = self.client.post(self.assign_tag_url,data,format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)

    def test_assign_tag_to_domain_success(self):
        self.client.force_authenticate(user=self.regular_user)
        data = [{
            'domain_name': 'github.com',
            'tag_title': 'PenetrationTesting'
        }]

        response = self.client.post(self.assign_tag_url,data,format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        db_check = User_Domain_Tag.objects.filter(
            user=self.regular_user,
            domain=self.public_domain.id,
            tag=self.sample_tag_1.id
        ).exists()
        self.assertTrue(db_check)
    def test_assign_tag_to_domain_conflict(self):
        self.client.force_authenticate(user=self.regular_user)
        data = [{
            'domain_name': 'google.com',
            'tag_title': 'HighSecurity'
        }]

        response = self.client.post(self.assign_tag_url,data,format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error_code'],60)

#patch method tests#
    def test_bad_req2_for_assign_tag_to_domain(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'domain_name': '',
            'tag_title': ''
        }

        response = self.client.patch(self.assign_tag_url,data,format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'],10)

    def test_assign_tag_to_domain_conflict2(self):
        self.client.force_authenticate(user=self.regular_user)
        data = [{
            'domain_name': 'github.com',
            'tag_title': 'PenetrationTesting',
            'confirm': True
        }]

        response = self.client.patch(self.assign_tag_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error_code'], 61)

    def test_patch_tag_same_as_existing(self):
        self.client.force_authenticate(user=self.regular_user)
        data = [{
            'domain_name': 'google.com',
            'tag_title': 'PenetrationTesting',
            'confirm': False
        }]
        response = self.client.patch(self.assign_tag_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_tag_requires_confirmation_code_21(self):
        self.client.force_authenticate(user=self.regular_user)
        data = [{
            'domain_name': 'google.com',
            'tag_title': 'HighSecurity',
            'confirm': False
        }]
        response = self.client.patch(self.assign_tag_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error_code'], 21)
        self.assertIn('requires_confirmation', response.data['detail'])

    def test_patch_tag_with_confirm_success(self):
        self.client.force_authenticate(user=self.regular_user)
        data = [{
            'domain_name': 'google.com',
            'tag_title': 'HighSecurity',
            'confirm': True
        }]
        response = self.client.patch(self.assign_tag_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        self.existing_relation.refresh_from_db()
        self.assertEqual(self.existing_relation.tag, self.sample_tag_2)
from django.urls import path

from accounts.views .register import UserRegisterView
from accounts.views.login import UserLoginView
from accounts.views.profile_update import ProfileUpdateView
from accounts.views.reset_pass import PasswordResetWithBackupCodeView
from accounts.views.get_my_role import ReturnTheRoleOfUser

from user_management.views .list_users import ListOfUsersView
from user_management.views .pending_users import PendingUsersView
from user_management.views .list_roles import ListOfRolesView
from user_management.views .assign_role import AssignUserRoleView
from user_management.views.manage_status import ManageUsersStatusView

from group_management.views.group_list import ListOfGroupsView
from group_management.views.group_register import GroupRegisterView
from group_management.views.group_detail import GroupDetailOREditView
from group_management.views.group_user_assign import AssignUsersGroups
from group_management.views.group_domains import GroupDomainView
from group_management.views.group_members import GroupMembersView
from group_management.views.group_domain_assign import  GroupDomainAssignView


from domain_tag_management.views.domain_list import DomainListView
from domain_tag_management.views.import_update_or_delete_domain import ImportOrEditDomainView
from domain_tag_management.views.tag_create import TagCreateView
from domain_tag_management.views.tag_list import ListOfTagView
from domain_tag_management.views.tag_edit_or_delete import TagUpdateView
from domain_tag_management.views.assign_tag_to_domain import BulkSyncDomainTagsView
from domain_tag_management.views.domain_detail import DomainDetailView



urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('reset-password/', PasswordResetWithBackupCodeView.as_view(), name="reset_password"),
    path('myRole/', ReturnTheRoleOfUser.as_view(), name='my_role'),

    path('admin/list-of-users/', ListOfUsersView.as_view(), name='list-of-users'),
    path('admin/list-of-pending-users/', PendingUsersView.as_view(), name='pending-users'),
    path('admin/list-of-roles/', ListOfRolesView.as_view(), name='list-of-roles'),

    path('super-admin/users/<int:pk>/assign/role/', AssignUserRoleView.as_view(), name='assign-users-role'),
    path('super-admin/users/<int:pk>/change/status/', ManageUsersStatusView.as_view(),name='manage-user-status'),

    path('list/', ListOfGroupsView.as_view(), name='list-of-groups'),
    path('create/', GroupRegisterView.as_view(), name='group-register'),
    path('<int:group_id>/domains/', GroupDomainView.as_view(), name='group-domains'),
    path('<int:pk>/detail', GroupDetailOREditView.as_view(), name='group-detail'),
    path('assign-users', AssignUsersGroups.as_view(), name='assign-users-group'),
    path('group/<int:group_id>/members/', GroupMembersView.as_view(), name='group-members-get'),
    path('group/<int:group_id>/members/<int:user_id>/', GroupMembersView.as_view(),name='group-member-delete'),
    path('group/<int:group_id>/domains/assign/', GroupDomainAssignView.as_view(),name='group-domain-assign'),



    path('domain/detail/list/', DomainListView.as_view(), name='list-of-domains'),
    path('import-or-edit/domain/', ImportOrEditDomainView.as_view(), name='domain-import/edit-bulk'),
    path('domain/<int:pk>/detail/', DomainDetailView.as_view(), name='domain-detail'),

    path('tag-assign-to-domain/', BulkSyncDomainTagsView.as_view(), name='assign-a-tag'),

    path('tag/create/', TagCreateView.as_view(), name='tag-create'),
    path('tag/detail/list', ListOfTagView.as_view(), name='list-of-tag'),
    path('tag/<int:pk>/edit/', TagUpdateView.as_view(), name='tag-detail'),

]
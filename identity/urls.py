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
from group_management.views.group_assign_users import AssignUsersGroups
from group_management.views.group_domains import GroupDomainView

from domain_tag_management.views.domain_list import DomainDetailView
from domain_tag_management.views.import_or_edit_domain import ImportOrEditDomainView
from domain_tag_management.views.tag_create import TagCreateView
from domain_tag_management.views.tag_list import ListOfTagView
from domain_tag_management.views.tag_edit_or_delete import TagUpdateView
from domain_tag_management.views.assign_tag_to_domain import BulkSyncDomainTagsView


urlpatterns = [
    path('account/register/', UserRegisterView.as_view(), name='register'),
    path('account/login/', UserLoginView.as_view(), name='login'),
    path('account/profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('account/reset-password/', PasswordResetWithBackupCodeView.as_view(), name="reset_password"),
    path('account/myRole/', ReturnTheRoleOfUser.as_view(), name='my_role'),

    path('user-managements/admin/list-of-users/', ListOfUsersView.as_view(), name='list-of-users'),
    path('user-managements/admin/list-of-pending-users/', PendingUsersView.as_view(), name='pending-users'),
    path('user-managements/admin/list-of-roles/', ListOfRolesView.as_view(), name='list-of-roles'),

    path('user-managements/super-admin/users/<int:pk>/assign/role/', AssignUserRoleView.as_view(), name='assign-users-role'),
    path('user-managements/super-admin/users/<int:pk>/change/status/', ManageUsersStatusView.as_view(),name='manage-user-status'),

    path('group-managements/list/', ListOfGroupsView.as_view(), name='list-of-groups'),
    path('group-managements/create/', GroupRegisterView.as_view(), name='group-register'),
    path('group-managements/<int:group_id>/domains/', GroupDomainView.as_view(), name='group-domains'),
    path('group-managements/<int:pk>/detail', GroupDetailOREditView.as_view(), name='group_detail'),
    path('group-managements/assign-users', AssignUsersGroups.as_view(), name='assign-users-group'),

    path('domain-managements/detail/list/', DomainDetailView.as_view(), name='list-of-domains'),
    path('domain-managements/import-or-edit/', ImportOrEditDomainView.as_view(), name='domain-import/edit-bulk'),

    path('tagmanagements/create/', TagCreateView.as_view(), name='tag-create'),
    path('tags-managements/list/', ListOfTagView.as_view(), name='list-of-tag'),
    path('tag-managements/<int:pk>/edit/', TagUpdateView.as_view(), name='tag-detail'),
    path('tags-managements/assign-to-domain/', BulkSyncDomainTagsView.as_view(), name='assign-a-tag'),

]
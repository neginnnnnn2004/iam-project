from django.urls import path
from .views import user_views, auth_views, group_views, domain_views, reset_pass_views

urlpatterns = [
    path('auth/register/', auth_views.UserRegisterView.as_view(), name='user-register'),
    path('auth/login/', auth_views.UserLoginView.as_view(), name='user-login'),
    path('auth/profile/update/', auth_views.ProfileUpdateView.as_view(), name='update-profile'),
    path('auth/password-reset/', reset_pass_views.PasswordResetWithBackupCodeView.as_view(),name='password_reset_confirm'),
    path('auth/myRole/', user_views.ReturnTheRoleOfUser.as_view(), name='user-profile-me'),

    path('admin/list-of-users/', user_views.ListOfUsersView.as_view(), name='list-of-users'),
    path('admin/list-of-pending-users/', user_views.PendingUsersView.as_view(), name='pending-users'),
    path('admin/list-of-roles/', user_views.ListOfRolesView.as_view(), name='list-of-roles'),
    path('admin/users/<int:pk>/assign/role/', user_views.AssignUserRoleView.as_view(), name='assign-users-role'),
    path('admin/users/<int:pk>/change/status/', user_views.ManageUsersStatusView.as_view(), name='manage-user-status'),
    path('admin/users/<int:pk>/make/active-or-inactive/', user_views.UserActivationView.as_view(), name='is-active'),

    path('group/list/', group_views.ListOfGroupsView.as_view(), name='list-of-groups'),
    path('group/create/', group_views.GroupRegisterView.as_view(), name='group-register'),
    path('group/<int:group_id>/domains/', group_views.GroupDomainView.as_view(), name='group-domains'),
    path('group/<int:pk>/detail', group_views.GroupDetailOREditView.as_view(), name='group_detail'),
    path('group/assign-users', group_views.AssignUsersGroups.as_view(), name='assign-users-group'),

    path('domains/detail/list/', domain_views.DomainDetailView.as_view(), name='list-of-domains'),
    path('domains/import-or-edit/', domain_views.ImportOrEditDomainView.as_view(), name='domain-import/edit-bulk'),

    path('tags/create/', domain_views.TagListCreateView.as_view(), name='tag-list-create'),
    path('tags/<int:pk>/detail/', domain_views.TagDetailView.as_view(), name='tag-detail'),
    path('tags/assign-to-domain/', domain_views.AssignTagToDomainView.as_view(), name='assign-a-tag'),
    path('tags/list/', domain_views.ListOfTagView.as_view(), name='list-of-tag'),

]
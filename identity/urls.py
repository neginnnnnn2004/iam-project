from django.urls import path
from .views import user_views, auth_views, group_views, domain_views, reset_pass_views, test_view

urlpatterns = [
    path('test/',test_view.TestView.as_view(), name='test'),


    path('register/', auth_views.UserRegisterView.as_view(), name='user-register'),
    path('login/', auth_views.UserLoginView.as_view(), name='user-login'),
    path('update/', auth_views.ProfileUpdateView.as_view(), name='update-profile'),

    path('listOfUsers', user_views.ListOfUsersView.as_view(), name='list-of-users'),
    path('pending/', user_views.PendingUsersView.as_view(), name='pending-users'),
    path('roles/', user_views.ListOfRolesView.as_view(), name='list-of-roles'),
    path('admin/users/<int:pk>/role/', user_views.AssignUserRoleView.as_view(), name='assign-users-role'),
    path('me/', user_views.ReturnTheRoleOfUser.as_view(), name='user-profile-me'),
    path('admin/users/<int:pk>/status/', user_views.ManageUsersStatusView.as_view(), name='manage-user-status'),
    path('admin/users/<int:pk>/is-active/', user_views.UserActivationView.as_view(), name='is-active'),

    path('listOfGroups/', group_views.ListOfGroupsView.as_view(), name='list-of-groups'),
    path('group-register/', group_views.GroupRegisterView.as_view(), name='group-register'),
    path('admin/groups/<int:pk>/detail', group_views.GroupDetailOREditView.as_view(), name='group_detail'),
    path('admin/users/group/', group_views.AssignUsersGroups.as_view(), name='assign-users-group'),
    path('groups/<int:group_id>/domains/', group_views.GroupDomainView.as_view(), name='group-domains'),

    path('domains/import_edit/', domain_views.ImportOrEditDomainView.as_view(), name='domain-import/edit-bulk'),
    path('listOfDomains/', domain_views.DomainDetailView.as_view(), name='list-of-domains'),
    path('tags/', domain_views.TagListCreateView.as_view(), name='tag-list-create'),
    path('listOfTag/', domain_views.ListOfTagView.as_view(), name='list-of-tag'),
    path('tags/<int:pk>/', domain_views.TagDetailView.as_view(), name='tag-detail'),
    path('assign-a-tag/', domain_views.AssignTagToDomainView.as_view(), name='assign-a-tag'),

    path('password-reset/confirm/', reset_pass_views.PasswordResetWithBackupCodeView.as_view(),name='password_reset_confirm'),
    ]
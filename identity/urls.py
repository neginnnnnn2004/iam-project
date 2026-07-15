from django.urls import path
from .views import user_views, auth_views, group_views, domain_views, reset_pass_views

urlpatterns = [
    path('register/', auth_views.UserRegisterView.as_view(), name='user-register'),
    path('login/', auth_views.UserLoginView.as_view(), name='user-login'),
    path('update/', auth_views.ProfileUpdateView.as_view(), name='update-profile'),

    path('', user_views.ListOfUsersView.as_view(), name='list-of-users'),
    path('pending/', user_views.PendingUsersView.as_view(), name='pending-users'),
    path('roles/', user_views.ListOfRolesView.as_view(), name='list-of-roles'),
    path('admin/users/<int:pk>/role/', user_views.AssignUserRoleView.as_view(), name='assign-users-role'),
    path('admin/users/<int:pk>/', user_views.ManageUsersStatusView.as_view(), name='manage-user-status'),
    path('admin/users/<int:pk>/is-active/', user_views.UserActivationView.as_view(), name='is-active'),

    path('listOfGroups/', group_views.ListOfGroupsView.as_view(), name='list-of-groups'),
    path('group-register/', group_views.GroupRegisterView.as_view(), name='group-register'),
    path('admin/groups/<int:pk>/', group_views.GroupDetailView.as_view(), name='group_detail'),
    path('admin/users/group/', group_views.AssignUsersGroups.as_view(), name='assign-users-group'),

    path('domain-register/', domain_views.ImportDomain.as_view(), name='domain-register'),
    path('listOfDomains/', domain_views.DomainDetail.as_view(), name='list-of-domains'),
    path('tag-register/', domain_views.CreateTag.as_view(), name='tag-register'),
    path('listOfTags/', domain_views.TagDetail.as_view(), name='list-of-tags'),
    path('assign-a-tag/', domain_views.AssignTagToDomain.as_view(), name='assign-a-tag'),

    path('password-reset/confirm/', reset_pass_views.PasswordResetWithBackupCodeView.as_view(),name='password_reset_confirm'),
    ]
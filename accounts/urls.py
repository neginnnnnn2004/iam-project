from django.urls import path
from accounts import views

urlpatterns = [
    path('', views.ListOfUsersView.as_view(), name='list-of-users'),
    path('register/', views.UserRegisterView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('pending/', views.PendingUsersView.as_view(), name='pending-users'),
    path('update/', views.ProfileUpdateView.as_view(), name='update-profile'),
    path('listOfGroups/', views.ListOfGroupsView.as_view(), name='list-of-groups'),
    path('group-register/', views.GroupRegisterView.as_view(), name='group-register'),
    path('admin/users/group/', views.AssignUsersGroups.as_view(), name='assign-users-group'),
    path('admin/users/<int:pk>/role/', views.AssignUserRoleView.as_view(), name='assign-users-role'),
    path('roles/', views.ListOfRolesView.as_view(), name='list-of-roles'),
    path('admin/users/<int:pk>/', views.ManageUsersStatusView.as_view(), name='manage-user-status'),
    path('admin/groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('admin/users/<int:pk>/is-active/', views.UserActivationView.as_view(), name='is-active'),
]

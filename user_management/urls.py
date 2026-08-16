from django.urls import path
from user_management.views .list_users import ListOfUsersView
from user_management.views .pending_users import PendingUsersView
from user_management.views .list_roles import ListOfRolesView
from user_management.views .assign_role import AssignUserRoleView
from user_management.views.manage_status import ManageUsersStatusView

urlpatterns = [
    path('user-managements/admin/list-of-users/', ListOfUsersView.as_view(), name='list-of-users'),
    path('user-managements/admin/list-of-pending-users/', PendingUsersView.as_view(), name='pending-users'),
    path('user-managements/admin/list-of-roles/', ListOfRolesView.as_view(), name='list-of-roles'),

    path('user-managements/super-admin/users/<int:pk>/assign/role/', AssignUserRoleView.as_view(), name='assign-users-role'),
    path('user-managements/super-admin/users/<int:pk>/change/status/', ManageUsersStatusView.as_view(),name='manage-user-status'),

]
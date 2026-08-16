from django.urls import path
from group_management.views.group_list import ListOfGroupsView
from group_management.views.group_register import GroupRegisterView
from group_management.views.group_detail import GroupDetailOREditView
from group_management.views.group_assign_users import AssignUsersGroups
from group_management.views.group_domains import GroupDomainView


urlpatterns =[
path('group-managements/list/', ListOfGroupsView.as_view(), name='list-of-groups'),
path('group-managements/create/', GroupRegisterView.as_view(), name='group-register'),
path('group-managements/<int:group_id>/domains/', GroupDomainView.as_view(), name='group-domains'),
path('group-managements/<int:pk>/detail', GroupDetailOREditView.as_view(), name='group-detail'),
path('group-managements/assign-users', AssignUsersGroups.as_view(), name='assign-users-group')
]

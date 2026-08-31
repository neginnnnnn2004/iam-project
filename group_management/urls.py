from django.urls import path
from group_management.views.group_list import ListOfGroupsView
from group_management.views.group_register import GroupRegisterView
from group_management.views.group_detail import GroupDetailOREditView
from group_management.views.group_user_assign import AssignUsersGroups
from group_management.views.group_domains import GroupDomainView
from group_management.views.group_members import GroupMembersListView
from group_management.views.group_members import GroupMemberDeleteView
from group_management.views.group_domain_assign import  GroupDomainAssignView

urlpatterns =[
    path('list/', ListOfGroupsView.as_view(), name='list-of-groups'),
    path('create/', GroupRegisterView.as_view(), name='group-register'),
    path('<int:group_id>/domains/', GroupDomainView.as_view(), name='group-domains'),
    path('<int:pk>/detail', GroupDetailOREditView.as_view(), name='group-detail'),
    path('assign-users', AssignUsersGroups.as_view(), name='assign-users-group'),
    path('group/<int:group_id>/members/', GroupMembersListView.as_view(), name='group-members-get'),
    path('group/<int:group_id>/members/<int:user_id>/', GroupMemberDeleteView.as_view(), name='group-member-delete'),
    path('group/<int:group_id>/domains/assign/', GroupDomainAssignView.as_view(), name='group-domain-assign'),
]

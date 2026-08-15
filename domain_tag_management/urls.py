from domain_tag_management.views.domain_list import DomainDetailView
from domain_tag_management.views.import_or_edit_domain import ImportOrEditDomainView
from domain_tag_management.views.tag_create import TagCreateView
from domain_tag_management.views.tag_list import ListOfTagView
from domain_tag_management.views.tag_edit_or_delete import TagUpdateView
from domain_tag_management.views.assign_tag_to_domain import BulkSyncDomainTagsView

from django.urls import path
urlpatterns = [
    path('domain-managements/detail/list/', DomainDetailView.as_view(), name='list-of-domains'),
    path('domain-managements/import-or-edit/', ImportOrEditDomainView.as_view(), name='domain-import/edit-bulk'),

    path('tagmanagements/create/', TagCreateView.as_view(), name='tag-create'),
    path('tags-managements/list/', ListOfTagView.as_view(), name='list-of-tag'),
    path('tag-managements/<int:pk>/edit/', TagUpdateView.as_view(), name='tag-detail'),
    path('tags-managements/assign-to-domain/', BulkSyncDomainTagsView.as_view(), name='assign-a-tag'),
]

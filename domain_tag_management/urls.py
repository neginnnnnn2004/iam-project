from domain_tag_management.views.domain_list import DomainListView
from domain_tag_management.views.import_update_or_delete_domain import ImportOrEditDomainView
from domain_tag_management.views.domain_detail import DomainDetailView
from domain_tag_management.views.tag_create import TagCreateView
from domain_tag_management.views.tag_list import ListOfTagView
from domain_tag_management.views.tag_edit_or_delete import TagUpdateView
from domain_tag_management.views.assign_tag_to_domain import BulkSyncDomainTagsView

from django.urls import path
urlpatterns = [
    path('domain/detail/list/', DomainListView.as_view(), name='list-of-domains'),
    path('import-or-edit/domain/', ImportOrEditDomainView.as_view(), name='domain-import/edit-bulk'),
    path('domain/<int:pk>/detail/', DomainDetailView.as_view(), name='domain-detail'),

    path('tag-assign-to-domain/', BulkSyncDomainTagsView.as_view(), name='assign-a-tag'),

    path('tag/create/', TagCreateView.as_view(), name='tag-create'),
    path('tag/detail/list', ListOfTagView.as_view(), name='list-of-tag'),
    path('tag/<int:pk>/edit/', TagUpdateView.as_view(), name='tag-detail'),

]

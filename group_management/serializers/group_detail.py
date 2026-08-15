from rest_framework import serializers
from identity.models import Group

class GroupSerializer(serializers.ModelSerializer):
    """
       Serializes a group with all its model fields.

       Administrative and system-managed fields are read-only and cannot be
       set through the API; they are populated automatically by the system.

       Attributes:
           All writable fields of the ``Group`` model (e.g. title,
           description, is_active, etc.).

       Read-only fields (auto-managed by the system):
           assigned_by: The user who assigned/created the group.
           deleted_at: Soft-delete timestamp.
           created_at: Creation timestamp.
           updated_at: Last update timestamp.
           updated_by: The user who last updated the group.
           code: A stable machine-readable code for the group.

       Example:
           >>> serializer = GroupSerializer(group)
           >>> serializer.data
           {'id': 1, 'code': 'admins', 'title': 'Admins', ...}
       """
    class Meta:
        model = Group
        fields = "__all__"
        read_only_fields = ["assigned_by", "deleted_at", "created_at", "updated_at", "updated_by", "code"]
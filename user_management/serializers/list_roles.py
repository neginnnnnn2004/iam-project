from rest_framework import serializers
from identity.models import Role

class ListOfRolesSerializer(serializers.ModelSerializer):
    """
    Serializes a list of roles for read-only display.

    This serializer is intended for listing roles (e.g. in a dropdown or
    an admin panel) and exposes the core identifying and descriptive
    fields of each role without any writable behavior.

    Attributes:
        id (serializers.IntegerField): The role's unique identifier.
        code (serializers.CharField): A stable machine-readable code for
            the role.
        title (serializers.CharField): The human-readable display title
            of the role.
        level (serializers.IntegerField): The role's hierarchy level.
        is_system (serializers.BooleanField): Whether the role is a
            system-defined role (cannot be modified/deleted).

    Example:
        >>> serializer = ListOfRolesSerializer(Role.objects.all(), many=True)
        >>> serializer.data
        [{'id': 1, 'code': 'admin', 'title': 'ادمین', 'level': 1, 'is_system': True}]
    """
    class Meta:
        model = Role
        fields = (
            'id',
            'code',
            'title',
            'level',
            'is_system',
        )

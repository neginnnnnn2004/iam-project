from rest_framework import serializers
from identity.models import Domain, Group


class DomainImportOrEditSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and editing a domain.

    This serializer handles the domain's basic information and allows
    associating the domain with one or more groups.

    The ``created_by`` field is read-only and exposes the username of
    the user who created the domain.

    Fields:
        domain_name (str):
            Name of the domain.

        description (str):
            Description of the domain.

        created_by (str):
            Username of the user who created the domain.
            This field is read-only.

        group (int):
            Primary key of the group associated with the domain.

    Notes:
        The ``created_by`` field cannot be provided or modified by the
        client.

        When groups are provided, they are resolved to existing
        ``Group`` instances by their primary keys.

    Example:
        Input:
            {
                "domain_name": "example.com",
                "description": "Example domain",
                "groups": [1, 2]
            }

        Output:
            {
                "domain_name": "example.com",
                "description": "Example domain",
                "created_by": "admin",
                "groups": [1, 2]
            }
    """

    created_by = serializers.ReadOnlyField(
        source='created_by.username'
    )

    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Domain
        fields = [
            'domain_name',
            'description',
            'created_by',
            'groups'
        ]
        read_only_fields = ['created_by']


class DomainDeleteSerializer(serializers.ModelSerializer):
    """
    Serializer for deleting a domain.

    This serializer identifies the domain that should be deleted
    by its domain name.

    Fields:
        domain_name (str):
            Name of the domain to be deleted.

    Notes:
        This serializer is intended to validate and receive the domain
        name required for the delete operation. The actual deletion
        logic is handled by the corresponding view or service.
    """

    class Meta:
        model = Domain
        fields = [
            'domain_name',
        ]
from rest_framework import serializers
from identity.models import Domain


class DomainImportOrEditSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new domain.

    This serializer handles the creation of a Domain instance and
    allows assigning the domain to one or more groups during creation.

    Fields:
        domain_name (str):
            The name of the domain.

        description (str):
            A description for the domain.

        created_by (str):
            The username of the user who created the domain.
            This field is read-only.

        groups (list):
            A list of groups associated with the domain.

    Notes:
        The `created_by` field is read-only and is populated from the
        related user's username.

        During creation, the provided groups are removed from the
        validated data, the Domain instance is created, and then the
        groups are assigned using `domain.groups.set()`.

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

    class Meta:
        model = Domain
        fields = [
            'domain_name',
            'description',
            'created_by',
            'groups'
        ]
        read_only_fields = ['created_by']

    def create(self, validated_data):
        """
        Create and return a new Domain instance.

        The groups are extracted from the validated data before creating
        the Domain instance. After the domain is created, the provided
        groups are assigned to it.

        Args:
            validated_data (dict):
                Validated data containing the domain information and
                optionally a list of groups.

        Returns:
            Domain:
                The newly created Domain instance.
        """
        groups = validated_data.pop('groups', [])

        domain = Domain.objects.create(**validated_data)

        if groups:
            domain.groups.set(groups)

        return domain
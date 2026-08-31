from rest_framework import serializers
from identity.models import Domain, Group


class DomainImportOrEditSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and editing a domain.

    This serializer handles the domain's basic information and allows
    associating the domain with a group.

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

    """

    created_by = serializers.ReadOnlyField(
        source='created_by.username'
    )

    group = serializers.PrimaryKeyRelatedField(
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
            'group'
        ]
        read_only_fields = ['created_by']


class DomainDeleteSerializer(serializers.Serializer):
    """
    Serializer for domain deletion requests.

    Used to validate the domain name required to identify the domain
    for deletion. Since this is an input-only serializer for
    deletion logic, it does not perform database-level uniqueness checks.

    Attributes:
        domain_name (str): The unique name of the domain to be deleted.
    """

    domain_name = serializers.CharField(required=True)
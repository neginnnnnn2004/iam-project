from rest_framework import serializers
from identity.models import Domain, Tag


class DomainRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new domain.

    Handles the creation of a Domain instance and allows assigning
    the domain to one or more groups during creation.

    Fields:
        domain_name (str):
            The name of the domain.

        description (str):
            A description of the domain.

        created_by (str):
            The username of the user who created the domain.
            This field is read-only.

        groups (list):
            A list of groups associated with the domain.

    Notes:
        The `created_by` field is read-only and is populated from the
        related user's username.

        During creation, the selected groups are extracted from the
        validated data and assigned to the domain after it is created.
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
        Create a new Domain instance and assign the selected groups.

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


class TagListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing tag information.

    Provides the main information of a tag, including its identifier,
    title, description, active status, and the username of the user
    who created it.

    Fields:
        id (int):
            The unique identifier of the tag.

        title (str):
            The title or name of the tag.

        description (str):
            A description of the tag.

        is_active (bool):
            Indicates whether the tag is currently active.

        created_by (str):
            The username of the user who created the tag.
            This field is read-only.
    """

    created_by = serializers.ReadOnlyField(
        source='created_by.username'
    )

    class Meta:
        model = Tag
        fields = [
            'id',
            'title',
            'description',
            'is_active',
            'created_by'
        ]
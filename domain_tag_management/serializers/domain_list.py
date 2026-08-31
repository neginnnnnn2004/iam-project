from rest_framework import serializers
from identity.models import Domain, Tag, Group


class GroupListSerializer(serializers.ModelSerializer):
    """
    Serializer for representing group information.

    This serializer is used to return basic information about a group
    when group are included in API responses.

    Fields:
        id (int):
            Unique identifier of the group.
        title (str):
            Display title of the group.
        description (str):
            Description of the group.
        is_active (bool):
            Indicates whether the group is currently active.
    """

    class Meta:
        model = Group
        fields = [
            'id',
            'title',
            'description',
            'is_active',
        ]


class DomainListSerializer(serializers.ModelSerializer):
    """
    Serializer for representing domain information.

    This serializer returns the main information of a domain, including
    its creator and associated group.

    The creator's username is returned instead of the complete user object.
    The ``created_by`` field is read-only and cannot be modified by the
    client.

    Fields:
        id (int):
            Unique identifier of the domain.
        domain_name (str):
            Name of the domain.
        description (str):
            Description of the domain.
        created_by (str):
            Username of the user who created the domain. Read-only.
        group (dict):
            Group associated with the domain. This field is read-only.
    """

    created_by = serializers.ReadOnlyField(
        source='created_by.username'
    )

    group = GroupListSerializer(read_only=True)

    class Meta:
        model = Domain
        fields = [
            'id',
            'domain_name',
            'description',
            'created_by',
            'group'
        ]
        read_only_fields = ['created_by']


class TagListSerializer(serializers.ModelSerializer):
    """
    Serializer for representing tag information.

    This serializer is used to return the basic information of a tag
    in API responses.

    Fields:
        id (int):
            Unique identifier of the tag.
        title (str):
            Title of the tag.
        description (str):
            Description of the tag.
        is_active (bool):
            Indicates whether the tag is currently active.
    """

    class Meta:
        model = Tag
        fields = [
            'id',
            'title',
            'description',
            'is_active'
        ]

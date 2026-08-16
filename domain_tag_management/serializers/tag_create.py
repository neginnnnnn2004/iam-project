from rest_framework import serializers
from identity.models import Tag


class TagRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new tag.

    Handles the creation of a Tag instance and provides the tag's
    basic information, including its title, description, active status,
    and the username of the user who created it.

    Fields:
        code (str):
            The unique code of the tag. This field is read-only and
            is generated automatically.

        title (str):
            The title or name of the tag.

        description (str):
            A description providing additional information about the tag.

        is_active (bool):
            Indicates whether the tag is currently active.

        created_by (str):
            The username of the user who created the tag.
            This field is read-only.

    Notes:
        The `code` and `created_by` fields are read-only and cannot be
        modified through this serializer.
    """

    created_by = serializers.ReadOnlyField(
        source='created_by.username'
    )

    class Meta:
        model = Tag
        fields = [
            'code',
            'title',
            'description',
            'is_active',
            'created_by'
        ]
        read_only_fields = [
            'created_by',
            'code'
        ]
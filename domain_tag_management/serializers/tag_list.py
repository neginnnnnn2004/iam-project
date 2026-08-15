from rest_framework import serializers
from identity.models import  Tag


class TagListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing tag information.

    Provides the main details of a tag, including its identifier,
    title, description, active status, and the username of the user
    who created it.

    Fields:
        id (int):
            The unique identifier of the tag.

        title (str):
            The title or name of the tag.

        description (str):
            A description providing additional information about the tag.

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
from rest_framework import serializers
from identity.models import Tag


class TagRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new tag.

    Handles validation and creation of a Tag instance and provides
    the tag's basic information, including its title, description,
    active status, and creator.

    Fields:
        id (int):
            Unique identifier of the tag.

        code (int):
            Unique code generated automatically for the tag.
            This field is read-only.

        title (str):
            Title or name of the tag.

        description (str):
            Additional information about the tag.

        is_active (bool):
            Indicates whether the tag is active.

        created_by (str):
            Username of the user who created the tag.
            This field is read-only.
    """

    created_by = serializers.ReadOnlyField(
        source='created_by.username'
    )

    class Meta:
        model = Tag
        fields = [
            'id',
            'code',
            'title',
            'description',
            'is_active',
            'created_by',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'deleted_at',
            'created_by',
            'code'
        ]

    def validate_title(self, value):
        """
        Validate that the normalized tag title is unique.

        Args:
            value (str):
                The tag title submitted by the client.

        Returns:
            str:
                The original tag title.

        Raises:
            serializers.ValidationError:
                If a tag with the same normalized title already exists.
        """
        normalized_title = value.strip().lower()

        queryset = Tag.objects.filter(
            title_normalized=normalized_title
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "A tag with this title already exists.",
                code='tag_exists'
            )

        return value
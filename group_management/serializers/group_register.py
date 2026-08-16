from rest_framework import serializers
from identity.models import Group

class GroupCreateSerializer(serializers.ModelSerializer):
    """
     Creates a new group with a unique title.

     Validates that the title (case-insensitive and whitespace-trimmed)
     does not already exist among groups, preventing duplicate entries.

     Attributes:
         title (serializers.CharField): The group's display title. Must be
             unique (compared case-insensitively after trimming).
         description (serializers.CharField): An optional description of
             the group.

     Raises:
         serializers.ValidationError: If a group with the same normalized
             title already exists.

     Example:
         >>> serializer = GroupCreateSerializer(data={'title': 'Backend', 'description': '...'})
         >>> serializer.is_valid()
         True
         >>> serializer.save()
     """
    class Meta:
        model = Group
        fields = ['title', 'description']

    def validate_title(self, value):
        if Group.objects.filter(title_normalized=value.strip().lower()).exists():
            raise serializers.ValidationError("این عنوان یا مشابه آن قبلاً ثبت شده است.")
        return value

class GroupResponseSerializer(serializers.ModelSerializer):

    class Meta:
        """
            Serializes a group for read-only response payloads.

            Exposes the group's identifying fields after creation or retrieval.

            Attributes:
                id (serializers.IntegerField): The group's unique identifier.
                title (serializers.CharField): The group's display title.
                code (serializers.CharField): A stable machine-readable code for
                    the group.

            Example:
                >>> serializer = GroupResponseSerializer(group)
                >>> serializer.data
                {'id': 1, 'title': 'Backend', 'code': 'backend'}
            """
        model = Group
        fields = ['id', 'title', 'code']
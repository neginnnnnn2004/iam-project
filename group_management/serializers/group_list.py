from rest_framework import serializers
from identity.models import Group

class AdminListOfGroupsSerializer(serializers.ModelSerializer):
    """
        Serializes groups for admin-side listing.

        Exposes the full set of group fields, including administrative flags
        such as activation state, for management and reporting purposes.

        Attributes:
            id (serializers.IntegerField): The group's unique identifier.
            code (serializers.CharField): A stable machine-readable code for
                the group.
            title (serializers.CharField): The group's display title.
            description (serializers.CharField): An optional description of
                the group.
            is_active (serializers.BooleanField): Whether the group is
                currently active.

        Example:
            >>> serializer = AdminListOfGroupsSerializer(Group.objects.all(), many=True)
            >>> serializer.data
            [{'id': 1, 'code': 'admins', 'title': 'Admins',
              'description': '...', 'is_active': True}]
        """
    class Meta:
        model = Group
        fields = ['id', 'code', 'title', 'description', 'is_active']

class UserListOfGroupsSerializer(serializers.ModelSerializer):
    """
       Serializes groups for user-facing listing.

       Exposes only the descriptive fields relevant to end users, omitting
       administrative metadata such as activation state and internal codes.

       Attributes:
           id (serializers.IntegerField): The group's unique identifier.
           title (serializers.CharField): The group's display title.
           description (serializers.CharField): An optional description of
               the group.

       Example:
           >>> serializer = UserListOfGroupsSerializer(Group.objects.all(), many=True)
           >>> serializer.data
           [{'id': 1, 'title': 'Admins', 'description': '...'}]
       """
    class Meta:
        model = Group
        fields = ['id', 'title', 'description']
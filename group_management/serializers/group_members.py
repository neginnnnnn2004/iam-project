from rest_framework import serializers
from identity.models import UserGroup

class GroupMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for a single membership entry when listing the users
    assigned to a group (admin-facing).
    """

    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    assigned_by = serializers.CharField(source='assigned_by.username', read_only=True)

    class Meta:
        model = UserGroup
        fields = [
            'id',
            'user_id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_primary',
            'assigned_by',
            'created_at',
        ]
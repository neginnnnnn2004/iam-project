from rest_framework import serializers
from identity.models import  UserGroup

class UserGroupSerializer(serializers.ModelSerializer):
    """
       Serializes the assignment of a user to a group.

       Enforces the business rule that a user can have at most one primary
       group. If ``is_primary`` is set to ``True`` and the user already has
       another primary group, validation fails.

       Attributes:
           user (serializers.PrimaryKeyRelatedField): The user being
               assigned (writable).
           group (serializers.PrimaryKeyRelatedField): The group to assign
               (writable).
           is_primary (serializers.BooleanField): Whether this is the user's
               primary group (writable).

       Read-only fields:
           assigned_by: The user who made the assignment (auto-filled).

       Raises:
           serializers.ValidationError: If the user already has a primary
               group and ``is_primary`` is set to ``True``.

       Example:
           >>> serializer = UserGroupSerializer(
           ...     data={'user': 1, 'group': 2, 'is_primary': True})
           >>> serializer.is_valid()
           True
           >>> serializer.save()
       """
    class Meta:
        model = UserGroup
        fields = ['user', 'group', 'is_primary','assigned_by']
        read_only_fields = ["assigned_by"]

    def validate(self, data):
        user = data.get('user')
        if data.get('is_primary'):
            qs = UserGroup.objects.filter(user=user, is_primary=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"is_primary": "کاربر در حال حاضر یک گروه اصلی دارد."})
        return data
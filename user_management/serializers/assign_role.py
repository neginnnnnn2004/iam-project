from rest_framework import serializers
from identity.models import User, Role

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """
       Updates the role of a target user by accepting the new role's ID.

       Both the target user and the role are identified by their IDs: the
       target user is passed via the URL (e.g. ``/api/users/{user_id}/role/``)
       while the new role is sent as an ID in the request body.

       The serializer exposes ``role`` as a writable field (the role ID to
       assign) and ``role_name`` as a read-only field that reflects the title
       of the currently assigned role, making the response more readable.

       Attributes:
           role (serializers.PrimaryKeyRelatedField): The ID of the role to
               assign to the target user (writable).
           role_name (serializers.CharField): The display title of the assigned
               role (read-only, sourced from ``role.title``).

       Example:
           >>> serializer = UserRoleUpdateSerializer(user, data={'role': 2})
           >>> serializer.is_valid()
           True
           >>> serializer.save()
           >>> serializer.data
           {'role': 2, 'role_name': 'Admin'}
       """
    role_name = serializers.CharField(source='role.title', read_only=True)

    class Meta:
        model = User
        fields = ['role', 'role_name']
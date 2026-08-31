from rest_framework import serializers
from identity.models import User

class ReturnRoleUsersSerializer(serializers.ModelSerializer):
    """
       Serializer for returning user objects with their associated role details.

       This serializer flattens the related ``Role`` object into the user
       representation by exposing three additional read-only fields
       (``role_id``, ``role_code``, ``role_title``). This avoids nested
       serialization and provides a flat, frontend-friendly response structure
       where role information is directly accessible on the user object.

       Attributes:
           role_id (serializers.IntegerField): The primary key of the user's role.
           role_code (serializers.CharField): The system-level code of the role
               (e.g., 'admin', 'regular').
           role_title (serializers.CharField): The human-readable display title
               of the role (e.g., 'ادمین').

       Meta:
           model (User): The Django model being serialized.
           fields (tuple): The subset of user fields included in the output,
               along with the three flattened role fields.

       Example:
           >>> serializer = ReturnRoleUsersSerializer(user)
           >>> serializer.data
           {
               'id': 1,
               'username': 'admin_dara',
               'email': 'admin@test.com',
               'phone': '09111111111',
               'first_name': 'Dara',
               'last_name': 'Zamani',
               'role_id': 2,
               'role_code': 'admin',
               'role_title': 'ادمین'
           }
       """

    role_id = serializers.IntegerField(source='role.id', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)
    role_title = serializers.CharField(source='role.title', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'phone',
            'first_name',
            'last_name',
            'role_id',
            'role_code',
            'role_title',
        )
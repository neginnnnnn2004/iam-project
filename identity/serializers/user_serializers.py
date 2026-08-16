# from rest_framework import serializers
# from identity.models import User, Role
#
#
# class ListOfUsersSerializer(serializers.ModelSerializer):
#     """
#     Provides basic profile and contact information for user listing and reporting.
#     """
#
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'email', 'phone', 'first_name', 'last_name')
#
#
# class UserRoleUpdateSerializer(serializers.ModelSerializer):
#     """
#     Allows changing the user's role ID while returning the updated role's
#     title as a read-only field in the response payload.
#
#     Attributes:
#         role_name (serializers.CharField): The display title of the assigned role.
#     """
#
#     role_name = serializers.CharField(source='role.title', read_only=True)
#
#     class Meta:
#         model = User
#         fields = ['role', 'role_name']
#
# class UserStatusUpdateSerializer(serializers.ModelSerializer):
#     """
#     Used by administrators to modify account state (e.g., active, pending, suspended).
#     """
#
#     class Meta:
#         model = User
#         fields = ['status']
#
# class ListOfRoleUsersSerializer(serializers.ModelSerializer):
#     """
#     Includes role details (ID, code, title) directly in the user object representation
#     to optimize response structures for frontend consumption.
#
#     Attributes:
#         role_id (serializers.IntegerField): Unique identifier of the role.
#         role_code (serializers.CharField): System code associated with the role.
#         role_title (serializers.CharField): Human-readable title of the role.
#     """
#
#     role_id = serializers.IntegerField(source='role.id', read_only=True)
#     role_code = serializers.CharField(source='role.code', read_only=True)
#     role_title = serializers.CharField(source='role.title', read_only=True)
#
#     class Meta:
#         model = User
#         fields = (
#             'id',
#             'username',
#             'email',
#             'phone',
#             'first_name',
#             'last_name',
#             'role_id',
#             'role_code',
#             'role_title',
#         )
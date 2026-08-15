from rest_framework import serializers
from identity.models import User


class ListOfUsersSerializer(serializers.ModelSerializer):
    """
        Serializes a list of users with their basic profile and contact info.

        This serializer is intended for read-only user listing and reporting
        (e.g. admin panels, user directories) and exposes identifying and
        contact fields without any sensitive or writable data.

        Attributes:
            id (serializers.IntegerField): The user's unique identifier.
            username (serializers.CharField): The user's login username.
            email (serializers.EmailField): The user's email address.
            phone (serializers.CharField): The user's phone number.
            first_name (serializers.CharField): The user's first name.
            last_name (serializers.CharField): The user's last name.

        Example:
            >>> serializer = ListOfUsersSerializer(User.objects.all(), many=True)
            >>> serializer.data
            [{'id': 1, 'username': 'ali', 'email': 'ali@example.com',
              'phone': '0912...', 'first_name': 'Ali', 'last_name': 'Rezaei'}]
        """

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'first_name', 'last_name')

from rest_framework import serializers

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for validating the user login request payload.

    This serializer receives and validates the credentials submitted by a
    user during the login process. It ensures that both ``username`` and
    ``password`` are present and are valid strings before the authentication
    logic is executed.

    Attributes:
        username (serializers.CharField): The user's unique username or
            identifier used for authentication.
        password (serializers.CharField): The user's plain-text password.
            Note: this field is write-only in practice and should never be
            returned in responses.

    Example:
        >>> serializer = UserLoginSerializer(data={
        ...     'username': 'admin_dara',
        ...     'password': 'secret123'
        ... })
        >>> serializer.is_valid()
        True
        >>> serializer.validated_data
        {'username': 'admin_dara', 'password': 'secret123'}
    """
    username = serializers.CharField()
    password = serializers.CharField()
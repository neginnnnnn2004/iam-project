from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class PasswordResetWithBackupCodeSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    backup_code = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8, write_only=True)
    confirm_password = serializers.CharField(required=True, min_length=8, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "رمز عبور جدید و تکرار آن مطابقت ندارند."
            })
        return attrs
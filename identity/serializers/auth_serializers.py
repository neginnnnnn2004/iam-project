from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from identity.models import User
from django.core.validators import RegexValidator


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'phone', 'first_name', 'last_name')

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email already exists.')
        return email

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone already exists.")
        return value

    def validators_username(self,value):
        username = value.lower()
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists.")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="شماره تلفن وارد شده معتبر نیست. فرمت صحیح: 09123456789 یا +989123456789"
)
class ProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    last_name = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    phone= serializers.CharField(
        required=False,
        trim_whitespace=True,
        allow_blank=False,
        validators=[phone_regex]
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'password','phone')

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_phone(self, value):
        query = User.objects.filter(phone=value)
        if self.instance:
            query=query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("این شماره تلفن قبلاً ثبت شده است.")
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class ProfileUpdateResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    data = ProfileUpdateSerializer()
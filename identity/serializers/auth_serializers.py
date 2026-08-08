from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from identity.models import User
import re

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password','confirm_password', 'email', 'phone', 'first_name', 'last_name')

    def validate_username(self,value):
        username = value.lower()
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("این نام کاربری قبلا ثبت شده است")
        return username

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        if value:
            email = value.lower()
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError('این آدرس ایمیل از قبل ثبت شده است.')
            return email
        return value

    def validate_phone(self, value):
        if value:
            value = value.strip()

            if not re.match(r'^09\d{9}$', value):
                raise serializers.ValidationError(
                    "شماره تلفن باید با 09 شروع و 11 رقم باشد."
                )

            if User.objects.filter(phone=value).exists():
                raise serializers.ValidationError(
                    "این شماره تلفن قبلاً ثبت شده است."
                )

        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "رمز عبور و تکرار آن مطابقت ندارند"
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class ProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False,allow_blank=True,trim_whitespace=True)
    last_name = serializers.CharField(required=False,allow_blank=True,trim_whitespace=True)
    password = serializers.CharField(write_only=True,required=False,allow_blank=True,style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True,required=False,allow_blank=True,style={'input_type': 'password'})
    phone = serializers.CharField(required=False,trim_whitespace=True,allow_blank=True,)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'password', 'confirm_password', 'phone')

    def validate_password(self, value):
        if value and value.strip():
            validate_password(value)
        return value

    def validate_phone(self, value):
        if value and value.strip():
            value = value.strip()
            if not re.match(r'^09\d{9}$', value):
                raise serializers.ValidationError(
                    "شماره تلفن باید با 09 شروع و 11 رقم باشد."
                )
            if self.instance:
                if User.objects.filter(phone=value).exclude(pk=self.instance.pk).exists():
                    raise serializers.ValidationError(
                        "این شماره تلفن قبلاً ثبت شده است."
                    )
            else:
                if User.objects.filter(phone=value).exists():
                    raise serializers.ValidationError(
                        "این شماره تلفن قبلاً ثبت شده است."
                    )
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')


        if password is not None and password != '':
            if confirm_password is None or confirm_password == '':
                raise serializers.ValidationError({
                    "confirm_password": "برای تغییر رمز عبور، تکرار رمز عبور الزامی است."
                })
            if password != confirm_password:
                raise serializers.ValidationError({
                    "confirm_password": "رمز عبور و تکرار آن مطابقت ندارند"
                })

        if confirm_password is not None and confirm_password != '':
            if password is None or password == '':
                raise serializers.ValidationError({
                    "password": "برای تغییر رمز عبور، رمز عبور جدید الزامی است."
                })

        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)

        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class ProfileUpdateResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    data = ProfileUpdateSerializer()
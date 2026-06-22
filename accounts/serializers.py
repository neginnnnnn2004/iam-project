import hashlib

from rest_framework import serializers
from unicodedata import normalize

from accounts.models import User, Group, UserGroup, Role


class ListOfUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email','phone', 'first_name', 'last_name')

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'password',
            'email',
            'phone',
            'first_name',
            'last_name',
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            phone=validated_data.get('phone'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name')
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name','phone')

class ListOfGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id' , 'code' ,'title','description','is_active']
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"
        read_only_fields = ["assigned_by", "deleted_at","created_at","updated_at","updated_by","code"]
class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = ['user', 'group','is_primary']
        read_only_fields = ["assigned_by"]
    def validate(self, data):
        user = data.get('user')
        is_primary = data.get('is_primary')

        if is_primary:
            qs = UserGroup.objects.filter(user=user, is_primary=True)

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "is_primary": "کاربر در حال حاضر یک گروه اصلی دارد."
                })
        return data

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['role']

class listOfRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
class UserStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status' , instance.status)
        instance.save()
        return instance

class UserActivationSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class ProfileUpdateResponseSerializer(serializers.Serializer) :
    message = serializers.CharField()
    data = ProfileUpdateSerializer()

from rest_framework import serializers
from accounts.models import Group


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['title', 'description']

    def validate_title(self, value):
        normalized = value.strip().lower()

        if Group.objects.filter(title_normalized=normalized).exists():
            raise serializers.ValidationError(
                "این عنوان یا مشابه آن قبلاً ثبت شده است."
            )

        return value

class GroupResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id','title','code']

class ProfileUpdateResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    data = ProfileUpdateSerializer()
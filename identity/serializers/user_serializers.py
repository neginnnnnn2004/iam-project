from rest_framework import serializers
from identity.models import User, Role

class ListOfUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'first_name', 'last_name')

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.title', read_only=True)

    class Meta:
        model = User
        fields = ['role', 'role_name']

class listOfRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class UserStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']

class UserActivationSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class ListOfRoleUsersSerializer(serializers.ModelSerializer):
    role_id = serializers.IntegerField(source='role.id', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)
    role_title = serializers.CharField(source='role.title', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'first_name', 'last_name','role_id','role_code','role_title')
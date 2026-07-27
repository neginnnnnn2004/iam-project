from rest_framework import serializers
from rest_framework.utils import representation

from identity.models import User, Role

class ListOfUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'first_name', 'last_name')

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    role = serializers.SlugRelatedField(
        slug_field='title',
        queryset=Role.objects.all(),
        error_messages={
            'does_not_exist': 'نقشی با این عنوان یافت نشد.'
        }
    )
    class Meta:
        model = User
        fields = ['role']

    def  to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.role:
            representation['role'] = {
                'id': instance.role.id,
                'title': instance.role.title
            }
        return representation

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
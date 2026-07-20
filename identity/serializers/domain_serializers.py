from rest_framework import serializers
from identity.models import Domain, Tag, User_Domain_Tag

class DomainRegisterSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    class Meta:
        model = Domain
        fields = ['domain_name', 'description', 'created_by', 'groups']
        read_only_fields = ['created_by']

    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        domain = Domain.objects.create(**validated_data)
        if groups:
            domain.groups.set(groups)
        return domain

class TagRegisterSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    class Meta:
        model = Tag
        fields = ['code', 'title', 'description', 'is_active', 'created_by']
        read_only_fields = ['created_by', 'code']

class UserDomainTagSerializer(serializers.ModelSerializer):
    domain_name = serializers.SlugRelatedField(slug_field='domain_name', queryset=Domain.objects.all(), source='domain')
    title = serializers.SlugRelatedField(slug_field='title', queryset=Tag.objects.all(), source='tag')
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = User_Domain_Tag
        fields = ['user', 'domain_name', 'title', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user_id'] = self.context['request'].user.id
        return User_Domain_Tag.objects.create(**validated_data)

class UserDomainTagPatchSerializer(UserDomainTagSerializer):
    confirm = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = UserDomainTagSerializer.Meta.model
        fields = UserDomainTagSerializer.Meta.fields + ['confirm']
from rest_framework import serializers
from identity.models import Domain, Tag,Group


class GroupListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            'id',
            'title',
            'description',
            'is_active',
        ]

class DomainListSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(
        source='created_by.username'
    )

    groups = GroupListSerializer(read_only=True)

    class Meta:
        model = Domain
        fields = [
            'domain_name',
            'description',
            'created_by',
            'groups'
        ]
        read_only_fields = ['created_by']


class TagListSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(
        source='created_by.username'
    )

    class Meta:
        model = Tag
        fields = [
            'id',
            'title',
            'description',
            'is_active'
        ]


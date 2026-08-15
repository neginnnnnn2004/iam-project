from rest_framework import serializers
from identity.models import Domain

class DomainRegisterSerializer(serializers.ModelSerializer):
    """
    Registers a new domain and optionally associates it with groups.

    The ``created_by`` field is populated automatically from the
    authenticated request user and is read-only.

    Attributes:
        domain_name (serializers.CharField): The domain's name (writable).
        description (serializers.CharField): An optional description of
            the domain (writable).
        created_by (serializers.ReadOnlyField): The username of the user
            who created the domain (read-only, auto-filled).
        groups (serializers.PrimaryKeyRelatedField): Optional groups to
            associate with the domain (writable).

    Example:
        >>> serializer = DomainRegisterSerializer(
        ...     data={'domain_name': 'example.com', 'groups': [1, 2]},
        ...     context={'request': request})
        >>> serializer.is_valid()
        True
        >>> domain = serializer.save()
    """
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
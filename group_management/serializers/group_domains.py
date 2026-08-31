from rest_framework import serializers
from identity.models import Domain,Group

class DomainRegisterSerializer(serializers.ModelSerializer):
    """
    Registers a new domain and optionally associates it with a group.

    The ``created_by`` field is populated automatically from the
    authenticated request user and is read-only.

    Attributes:
        domain_name (serializers.CharField): The domain's name (writable).
        description (serializers.CharField): An optional description of
            the domain (writable).
        created_by (serializers.ReadOnlyField): The username of the user
            who created the domain (read-only, auto-filled).
        group (serializers.PrimaryKeyRelatedField): Optional group to
            associate with the domain (writable).
    """
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        required=False,
        allow_null=True,
    )
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Domain
        fields = ['domain_name', 'description', 'created_by', 'group']
        read_only_fields = ['created_by']\

    def create(self, validated_data):
        """
        The creating user is automatically added when saving
        """
        user = self.context['request'].user
        return Domain.objects.create(created_by=user, **validated_data)

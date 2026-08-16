from rest_framework import serializers
from identity.models import User_Domain_Tag, Domain, Tag


class UserDomainTagSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a user-specific tag assignment to a domain.

    Converts the domain name and tag title provided by the client into
    their corresponding Domain and Tag model instances.

    The user is automatically determined from the authenticated request
    and cannot be specified or modified by the client.
    """

    domain_name = serializers.SlugRelatedField(
        slug_field='domain_name',
        queryset=Domain.objects.all(),
        source='domain'
    )

    title = serializers.SlugRelatedField(
        slug_field='title',
        queryset=Tag.objects.all(),
        source='tag'
    )

    user = serializers.ReadOnlyField(
        source='user.username'
    )

    class Meta:
        model = User_Domain_Tag
        fields = [
            'user',
            'domain_name',
            'title',
            'created_at',
            'updated_at'
        ]

    def create(self, validated_data):
        """
        Create a User_Domain_Tag for the authenticated user.

        Args:
            validated_data (dict):
                Validated domain and tag data.

        Returns:
            User_Domain_Tag:
                The newly created domain-tag relationship.
        """
        validated_data['user_id'] = self.context['request'].user.id

        return User_Domain_Tag.objects.create(**validated_data)


class UserDomainTagPatchSerializer(serializers.Serializer):
    """
    Serializer for updating a user's tag assigned to a domain.

    The old tag identifies which existing user-domain-tag relationship
    should be updated, while the new title specifies the replacement tag.

    Fields:
        domain_name:
            The name of the target domain.

        old_title:
            The title of the existing tag that should be replaced.

        title:
            The title of the new tag.

        confirm:
            Indicates whether the user has confirmed the requested change.
    """

    domain_name = serializers.CharField()

    old_title = serializers.CharField()

    title = serializers.CharField()

    confirm = serializers.BooleanField(
        required=False,
        default=False
    )


class BulkSyncDomainTagsSerializer(serializers.Serializer):
    """
    Serializer for synchronizing multiple domain-tag changes in one request.

    Supports adding, updating, and deleting multiple user-domain-tag
    relationships through a single API request.

    Fields:
        add:
            List of domain tags to be added.

        update:
            List of existing domain tags to be updated.

        delete:
            List of domain tags to be soft-deleted.
    """

    add = UserDomainTagSerializer(
        many=True,
        required=False,
        default=list
    )

    update = UserDomainTagPatchSerializer(
        many=True,
        required=False,
        default=list
    )

    delete = UserDomainTagSerializer(
        many=True,
        required=False,
        default=list
    )
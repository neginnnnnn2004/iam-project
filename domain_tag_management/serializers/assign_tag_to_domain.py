from rest_framework import serializers


class UserDomainTagAddSerializer(serializers.Serializer):
    """
    Serializer for a single domain-tag "add" or "delete" operation
    within a bulk sync request.
    """
    domain_name = serializers.CharField()
    title = serializers.CharField()


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

    add = UserDomainTagAddSerializer(
        many=True,
        required=False,
        default=list
    )

    update = UserDomainTagPatchSerializer(
        many=True,
        required=False,
        default=list
    )

    delete = UserDomainTagAddSerializer(
        many=True,
        required=False,
        default=list
    )
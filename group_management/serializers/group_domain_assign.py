from rest_framework import serializers


class DomainRefSerializer(serializers.Serializer):
    """
    Reference to a domain by name, used for bulk assign/unassign
    operations within a group.
    """
    domain_name = serializers.CharField()


class GroupDomainAssignSerializer(serializers.Serializer):
    """
    Serializer for bulk assigning/unassigning domains to/from a group.

    Fields:
        add:
            List of domains to assign to this group.

        remove:
            List of domains to unassign from this group
            (their `groups` field is set to null).
    """
    add = DomainRefSerializer(many=True, required=False, default=list)
    remove = DomainRefSerializer(many=True, required=False, default=list)
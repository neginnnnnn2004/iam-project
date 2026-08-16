from rest_framework import serializers
from identity.models import User, Role

class UserStatusUpdateSerializer(serializers.ModelSerializer):
    """
       Updates the account status of a target user.

       Used by administrators to modify the account state (e.g. active,
       pending, suspended). The target user is identified by its ID via the
       URL (e.g. ``/api/users/{user_id}/status/``) and the new status is sent
       in the request body.

       Attributes:
           status (serializers.ChoiceField): The new account status to assign
               to the target user (writable).

       Example:
           >>> serializer = UserStatusUpdateSerializer(user, data={'status': 'suspended'})
           >>> serializer.is_valid()
           True
           >>> serializer.save()
           >>> serializer.data
           {'status': 'suspended'}
       """

    class Meta:
        model = User
        fields = ['status']
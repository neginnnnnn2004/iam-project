from rest_framework import serializers
from identity.models import Group, UserGroup

class ListOfGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'code', 'title', 'description', 'is_active']

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"
        read_only_fields = ["assigned_by", "deleted_at", "created_at", "updated_at", "updated_by", "code"]

class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['title', 'description']

    def validate_title(self, value):
        if Group.objects.filter(title_normalized=value.strip().lower()).exists():
            raise serializers.ValidationError("این عنوان یا مشابه آن قبلاً ثبت شده است.")
        return value

class GroupResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'title', 'code']

class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = ['user', 'group', 'is_primary']
        read_only_fields = ["assigned_by"]

    def validate(self, data):
        user = data.get('user')
        if data.get('is_primary'):
            qs = UserGroup.objects.filter(user=user, is_primary=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"is_primary": "کاربر در حال حاضر یک گروه اصلی دارد."})
        return data
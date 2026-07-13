from django.contrib import admin
from .models import User,Role,Group,UserGroup,Domain,Tag,User_Domain_Tag

admin.site.register(User)
admin.site.register(Role)
admin.site.register(Group)
admin.site.register(UserGroup)
admin.site.register(Domain)
admin.site.register(Tag)
admin.site.register(User_Domain_Tag)


from django.contrib import admin
from django.contrib.auth.admin import  UserAdmin
from .models import User,Role,Group,UserGroup

admin.site.register(User)
admin.site.register(Role)
admin.site.register(Group)
admin.site.register(UserGroup)

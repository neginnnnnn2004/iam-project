from django.urls import path
from accounts.views .register import UserRegisterView
from accounts.views.login import UserLoginView
from accounts.views.profile_update import ProfileUpdateView
from accounts.views.reset_pass import PasswordResetWithBackupCodeView
from accounts.views.get_my_role import ReturnTheRoleOfUser


urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('reset-password/', PasswordResetWithBackupCodeView.as_view(), name="reset_password"),
    path('myRole/', ReturnTheRoleOfUser.as_view(), name='my_role'),

]

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

from identity.models import User as CustomUser
from identity.utils import generate_reset_token, verify_reset_token
# from identity.models import User
User = get_user_model()

class PasswordResetRequestView(APIView):
    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({'error': 'username required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user: CustomUser = User.objects.get(username=username.lower(), status='active')
            token = generate_reset_token(user.username)
            email_body = f"Hi {user.username} , \n\n(ValidTime:10 min)your token code for reset your password is:\n\n {token}"
            send_mail(
                subject='Reset Your Password',
                message=email_body,
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False
            )
        except User.DoesNotExist:
            pass
        return Response({
            "message": "if username is valid, reset token is sent to your email",
        }, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token or not new_password:
            return Response({"error": "token & newpass are required"}, status=status.HTTP_400_BAD_REQUEST)

        username = verify_reset_token(token, max_age_seconds=600)

        if not username:
            return Response({
                "error_code": 70,
                "message": "token is not valid or expired"
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            user: CustomUser = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()
            return Response({"message": "pass changed successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "user not found"}, status=status.HTTP_404_NOT_FOUND)
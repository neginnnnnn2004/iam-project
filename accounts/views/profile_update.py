from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers.profile_update import (
    ProfileUpdateSerializer,
    ProfileUpdateResponseSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from identity.services import log_critical_event

# ================== Profile Update =====================
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, partial=False):
        user = request.user

        serializer = ProfileUpdateSerializer(
            instance=user,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            serializer.save()

            # Check which sensitive fields were actually modified and verified
            important_fields = ['phone', 'password']
            changed_important = [f for f in serializer.validated_data.keys() if f in important_fields]

            if changed_important:
                # Log successful changes to sensitive profile information
                log_critical_event(
                    action='profile_update',
                    status_type='success',
                    request=request,
                    user_id=user.id,
                    extra={
                        'username': user.username,
                        'changed_sensitive_fields': changed_important,
                    }
                )

            return Response({
                'message': {
                    "fa": "پروفایل با موفقیت بروزرسانی شد",
                    "en": "Profile updated successfully"
                },
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        errors = serializer.errors
        if 'password' in errors:
            error_code = 30
            error_message = {
                "fa": "رمز عبور وارد شده معتبر نیست",
                "en": "Invalid password provided"
            }

        elif 'confirm_password' in errors:
            error_code = 32
            error_message = {
                "fa": "تکرار رمز عبور معتبر نیست",
                "en": "Password confirmation does not match"
            }

        elif 'non_field_errors' in errors:
            non_field_str = str(errors['non_field_errors'])
            if any(keyword in non_field_str for keyword in ['رمز عبور', 'password', 'تطابق']):
                error_code = 30
                error_message = {
                    "fa": "رمز عبور وارد شده معتبر نیست",
                    "en": "Invalid password provided"
                }
            else:
                error_code = 10
                error_message = {
                    "fa": "اطلاعات ارسالی نامعتبر است",
                    "en": "Provided data is invalid"
                }

        elif 'phone' in errors and 'already registered' in str(errors['phone']).lower():
            error_code = 33
            error_message = {
                "fa": "شماره تلفن وارد شده تکراری است",
                "en": "Provided phone number is already in use"
            }

        elif 'phone' in errors:
            error_code = 31
            error_message = {
                "fa": "فرمت شماره تلفن نامعتبر است",
                "en": "Invalid phone number format"
            }

        else:
            error_code = 10
            error_message = {
                "fa": "ویرایش اطلاعات پروفایل انجام نشد.",
                "en": "Profile update failed."
            }

        # Log errors related to changing sensitive information such as passwords and phone numbers
        log_critical_event(
            action='profile_update',
            status_type='failed',
            request=request,
            user_id=user.id,
            error_code=error_code,
            extra={
                'username': user.username,
                'validation_errors': errors
            }
        )

        return Response({
            "error_code": error_code,
            "message": error_message,
            "detail": errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="""
        Partial update of user profile information.

        Custom error codes for this endpoint:
        - code 10: Invalid input data.
        - code 30: Provided password is invalid (weak or bad format).
        - code 31: Invalid phone number format.
        - code 32: Password and confirm_password do not match.
        - code 33: Phone number is already registered by another user.
        """,
        request_body=ProfileUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=ProfileUpdateResponseSerializer
            ),
            400: "Bad Request (Code 10,30,31,32,33)",
            401: "Unauthorized",
        }
    )
    def patch(self, request):
        return self.update(request, partial=True)

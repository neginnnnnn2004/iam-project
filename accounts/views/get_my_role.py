from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from accounts.serializers.get_my_role import (ReturnRoleUsersSerializer)

from drf_yasg.utils import swagger_auto_schema

from identity.services import log_critical_event

# ================== ReturnMyRole =====================
class ReturnTheRoleOfUser(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get authenticated user profile and role details",
        responses={
            200: ReturnRoleUsersSerializer(),
            401: "Unauthorized",
        }
    )
    def get(self, request):
        user = request.user

        try:
            serializer = ReturnRoleUsersSerializer(user)
            data = serializer.data

            log_critical_event(
                action='get_my_role',
                status_type='success',
                request=request,
                user_id=user.id,
                extra={
                    'username': user.username,
                    'role': user.role.title if user.role else None,
                }
            )
            return Response(data, status=status.HTTP_200_OK)

        except Exception:
            log_critical_event(
                action='get_my_role',
                status_type='failed',
                request=request,
                user_id=user.id,
                error_code=500,
                extra={
                    'username': user.username,
                }
            )
            return Response(
                {"detail": "An error occurred while fetching user role / خطایی در دریافت نقش کاربر رخ داده است."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
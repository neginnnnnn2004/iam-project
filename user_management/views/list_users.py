from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from identity.models import User
from identity.services import log_critical_event
from identity.permissions import IsAdminRole

from user_management.serializers.list_users import (ListOfUsersSerializer)

from drf_yasg.utils import swagger_auto_schema


# ==================  ListOfAllUsers =====================
class ListOfUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="Get list of all users for admin",
        responses={
            200: ListOfUsersSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self, request):
        try:
            users = User.objects.all()
            serializer = ListOfUsersSerializer(users, many=True)

            log_critical_event(
                action='list_users',
                status_type='success',
                request=request,
                user_id=request.user.id,
                extra={
                    'username': request.user.username,
                    'count': users.count(),
                },
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception:
            log_critical_event(
                action='list_users',
                status_type='error',
                request=request,
                user_id=request.user.id,
                error_code='LIST_USERS_FAILED',
            )
            return Response(
                {"detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

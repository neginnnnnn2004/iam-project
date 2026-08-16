from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from identity.models import Role
from identity.services import log_critical_event
from identity.permissions import IsAdminRole

from user_management.serializers.list_roles import ListOfRolesSerializer

import logging
logger = logging.getLogger(__name__)


class ListOfRolesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        action = 'ROLE_LIST'

        try:
            roles = Role.objects.all()
            serializer = ListOfRolesSerializer(roles, many=True)

            log_critical_event(
                action=action,
                status_type='success',
                request=request,
                user_id=request.user.id,
                extra={'role_count': roles.count()}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            log_critical_event(
                action=action,
                status_type='error',
                request=request,
                user_id=request.user.id,
                error_code=500,
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                }
            )
            return Response(
                {"detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

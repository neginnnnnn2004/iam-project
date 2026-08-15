from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import APIView

from identity.models import Tag
from domain_tag_management.serializers.tag_list import (TagListSerializer)

from drf_yasg.utils import swagger_auto_schema


# list of all tags
class ListOfTagView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all active tags available for user selection",
        responses={
            200: TagListSerializer(many=True),
            401: "Unauthorized",
        }
    )

    def get(self,request):
        tags= Tag.objects.filter(is_active=True,deleted_at__isnull=True).order_by('title')
        serializer = TagListSerializer(tags , many=True)
        return Response(serializer.data , status=status.HTTP_200_OK)
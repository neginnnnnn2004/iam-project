from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import APIView

from identity.models import Tag
from identity.permissions import IsAdminRole
from domain_tag_management.serializers.tag_create import (TagRegisterSerializer)

from drf_yasg.utils import swagger_auto_schema


# edit or delete the tag
class TagUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, pk):
        try:
            return Tag.objects.get(pk=pk)
        except Tag.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_description="""
        Edit a tag by ID, with admin access.

        Custom error codes:
        - code 10: The submitted information is incomplete or invalid.
        - code 55: The requested tag was not found.
        """,
        request_body=TagRegisterSerializer,
        responses={
            200: TagRegisterSerializer(),
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 55)"
        }
    )
    def patch(self, request, pk):
        tag = self.get_object(pk)
        if not tag:
            return Response({
            "error_code": 55,
                "message": {
                    "fa": f"تگی با شناسه {pk} یافت نشد.",
                    "en": f"Tag with ID {pk} was not found."
                },
            }, status = status.HTTP_404_NOT_FOUND)

        serializer = TagRegisterSerializer(tag, data=request.data,partial=True)
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": {
                    "fa": "اطلاعات ارسالی معتبر نیست.",
                    "en": "The submitted data is not valid."
                },
                "detail": serializer.errors
            },status=status.HTTP_400_BAD_REQUEST)

        updated_tag = serializer.save()
        return Response(TagRegisterSerializer(updated_tag).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""
        Soft-delete a tag by ID, with admin access.

        Custom error codes:
        - code 55: The requested tag was not found.
        """,
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 55)"
        }
    )
    def delete(self, request,pk):
        tag = self.get_object(pk)
        if not tag:
            return Response({
                "error_code": 55,
                "message": {
                    "fa": f"تگی با شناسه {pk} یافت نشد.",
                    "en": f"Tag with ID {pk} was not found."
                },
            },status=status.HTTP_404_NOT_FOUND)

        tag.deleted_at = timezone.now()
        tag.is_active = False
        tag.save(update_fields=["is_active", 'deleted_at'])

        return Response(status=status.HTTP_204_NO_CONTENT)

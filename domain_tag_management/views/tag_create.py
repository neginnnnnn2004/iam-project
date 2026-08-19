from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import APIView

from identity.permissions import IsAdminRole
from domain_tag_management.serializers.tag_create import (TagRegisterSerializer)

from drf_yasg.utils import swagger_auto_schema


# create tags
class TagCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(

        operation_description="""
        Create a new tag, with admin access.

        Custom error codes:
        - code 10: The submitted information is incomplete or invalid.
        -code 11: Tag already exists
        """,
        request_body=TagRegisterSerializer,
        responses={
            201: TagRegisterSerializer(),
            400: "Bad Request ",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def post(self, request):
        serializer = TagRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            if 'title' in serializer.errors:
                for error in serializer.errors['title']:
                    if getattr(error, 'code', None) =='tag_exists':
                        return Response({
                            "error_code": 11,
                            "message": {
                                "fa": "این تگ قبلاً ثبت شده است.",
                                "en": "This tag already exists."
                            },
                            "detail": serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "error_code": 10,
                "message": {
                    "fa": "اطلاعات ارسالی برای ایجاد تگ معتبر نیست.",
                    "en": "The submitted data for creating a tag is not valid."
                },
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        tag = serializer.save(created_by=request.user)
        return Response(TagRegisterSerializer(tag).data, status=status.HTTP_201_CREATED)

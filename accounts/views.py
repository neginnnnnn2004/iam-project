from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView
from .models import User,Role,Group,UserGroup
from .permissions import IsAdminRole
from .serializers import UserRegisterSerializer, UserLoginSerializer, ListOfUsersSerializer, ListOfGroupsSerializer, \
    UserGroupSerializer, UserRoleUpdateSerializer, listOfRoleSerializer, UserStatusUpdateSerializer, \
    GroupSerializer, ProfileUpdateSerializer , UserActivationSerializer , ProfileUpdateResponseSerializer , GroupCreateSerializer , GroupResponseSerializer ,ProfileUpdateResponseSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

#1 ListOfAllUsers
class ListOfUsersView(APIView):
    @swagger_auto_schema(
        operation_description="دریافت لیست تمام کاربران",
        responses={200:ListOfUsersSerializer(many=True)}
    )
    def get(self,request):
        users = User.objects.all()
        serializer = ListOfUsersSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#2 registration
class UserRegisterView(APIView):
    @swagger_auto_schema(
        operation_description="ثبت نام کاربر جدید",
        request_body=UserRegisterSerializer,
        responses={
            201: UserRegisterSerializer,
            400: "Bad Request"
        }
    )
    def post(self,request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#3 Login
class UserLoginView(APIView):
    @swagger_auto_schema(
        operation_description="ورود کاربر و دریافت توکن JWT",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: "Unauthorized"
        }
    )
    def post(self,request):
        serializer = UserLoginSerializer(data=request.data)
        #check the fields
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        #user authenticate
        user = authenticate(
            username = serializer.validated_data['username'],
            password = serializer.validated_data['password']
        )
        #if user not found
        if user is None:
            return Response(
                {"detail":"نام کاربری یا رمز عبور اشتباه است"} ,
                status=status.HTTP_401_UNAUTHORIZED
            )
        #create token
        refresh = RefreshToken.for_user(user)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh': str(refresh),
        },status=status.HTTP_200_OK)


#4 ListOfAllPendingUsers
class PendingUsersView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]

    @swagger_auto_schema(
        operation_description="دریافت لیست کاربران در انتظار تایید" ,
        responses={
            200: ListOfUsersSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self,request):
        users = User.objects.select_related('role').filter(status="pending")
        serializer = ListOfUsersSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#5 ProfileUpdate
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
            return Response({
                'message': 'پروفایل با موفقیت بروزرسانی شد',
                'data': serializer.data
            },status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="بروزرسانی کامل پروفایل کاربر",
        request_body=ProfileUpdateSerializer,
        responses={
            200: ProfileUpdateResponseSerializer,
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def put(self, request):
        return self.update(request, partial=False)

    @swagger_auto_schema(
        operation_description="بروزرسانی جزیی پروفایل کاربر" ,
        request_body=ProfileUpdateSerializer,
        responses={
            200: ProfileUpdateResponseSerializer,
            400: "BAD REQUEST",
            401:"Unauthorized",
        }
    )

    def patch(self, request):
        return self.update(request, partial=True)
#6 Group List
class ListOfGroupsView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]

    @swagger_auto_schema(
        operation_description="دریافت لیست گروه ها",
        responses={
            200: ListOfGroupsSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self,request):
        groups = Group.objects.all()
        serializer = ListOfGroupsSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
#7 Group Create
class GroupRegisterView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="ایجاد گروه جدید",
        request_body=GroupCreateSerializer,
        responses={
            201: GroupResponseSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def post(self, request):
        serializer = GroupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group = serializer.save()

        return Response(
            GroupResponseSerializer(group).data,
            status=status.HTTP_201_CREATED
        )
#8 Assign users to group by admin
class AssignUsersGroups(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="انتساب کاربران به یکی از گروه های موجود توسط ادمین",
        request_body=UserGroupSerializer,
        responses={
            201: openapi.Response(
                description="Assigned successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT
                        )
                    }
                )
            )
        }
    )
    def post(self, request):
        serializer = UserGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_group = serializer.save(assigned_by=request.user)

        return Response(
            {
                "message": "User assigned to group successfully",
                "data": UserGroupSerializer(user_group).data
            },
            status=status.HTTP_201_CREATED
        )

#9 Assign a role to users by admin
class AssignUserRoleView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]

    @swagger_auto_schema(
        operation_description="انتساب یک نقش از نقش های موجود به کاربر مورد نظر توسط ادمین",
        request_body=UserRoleUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Assigned successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            )
        }
    )

    def patch(self,request,pk ):
        user = get_object_or_404(User,pk=pk,deleted_at__isnull=True)

        serializer = UserRoleUpdateSerializer(user,data=request.data ,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                'message':"نقش کاربر با موفقیت بروزرسانی شد." ,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
#10 ListOfAllRoles
class ListOfRolesView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]

    @swagger_auto_schema(
        operation_description="دریافت لیست نقش ها",
        responses={
            200: listOfRoleSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )

    def get(self,request):
        role = Role.objects.all()
        serializer = listOfRoleSerializer(role, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
#11 change the user status
    #     ('unverified','Unverified'),
    #     ('pending','Pending'),
    #     ('active','Active'),
    #     ('suspended','Suspended'),
    #     ('deleted','Deleted'),
class ManageUsersStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, pk):
        return get_object_or_404(User, pk=pk, deleted_at__isnull=True)

    @swagger_auto_schema(
        operation_description="تغییر وضعیت کاربر",
        request_body=UserStatusUpdateSerializer,
        responses={
            200: openapi.Response(
                description="User status updated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            400: "Bad Request",
        }
    )

    def patch(self, request, pk):
        user = self.get_object(pk)

        serializer = UserStatusUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        update_user = serializer.save()

        return Response(
            {
                "message": f"وضعیت کاربر با موفقیت به {update_user.status} تغییر یافت.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="حذف نرم کاربر",
        responses={
            204: "No Content",
            401:"Unauthorized",
            403:"Forbidden",
        }
    )
    def delete(self, request, pk):
        user = self.get_object(pk)
        user.deleted_at = timezone.now()
        user.status = 'deleted'
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

#12 Group Detail, Update, Delete
class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, pk):
        return get_object_or_404(
            Group.objects.select_related('assigned_by'),
            pk=pk,
            deleted_at__isnull=True
        )

    @swagger_auto_schema(
        operation_description="دریافت جزئیات گروه",
        responses={
            200: GroupSerializer(),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self, request, pk):
        group = self.get_object(pk)
        serializer = GroupSerializer(group)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="ویرایش کامل گروه",
        request_body=GroupSerializer,
        responses={
            200: GroupSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def put(self, request, pk):
        return self.update(request, pk, partial=False)

    @swagger_auto_schema(
        operation_description="ویرایش جزئی گروه",
        request_body=GroupSerializer,
        responses={
            200: GroupSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def patch(self, request, pk):
        return self.update(request, pk, partial=True)

    def update(self, request, pk, partial=False):
        group = self.get_object(pk)

        serializer = GroupSerializer(
            group,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="حذف نرم گروه",
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def delete(self, request, pk):
        group = self.get_object(pk)
        group.deleted_at = timezone.now()
        group.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
#13 make user active or inactive
class UserActivationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="فعال یا غیرفعال کردن کاربر",
        request_body=UserActivationSerializer,
        responses={
            200: openapi.Response(
                description="activation changed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk, deleted_at__isnull=True)

        serializer = UserActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.is_active = serializer.validated_data['is_active']
        user.save(update_fields=['is_active'])

        return Response(
            {
                "message": "وضعیت کاربر تغییر کرد",
                "is_active": user.is_active
            },
            status=status.HTTP_200_OK
        )
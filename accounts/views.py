from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.utils import timezone

from rest_framework.views import APIView

from .models import User,Role,Group,UserGroup
from .permissions import IsAdminRole
from .serializers import UserRegisterSerializer, UserLoginSerializer, ListOfUsersSerializer, ListOfGroupsSerializer, \
    UserGroupSerializer, UserRoleUpdateSerializer, listOfRoleSerializer, UserStatusUpdateSerializer, \
    GroupSerializer, ProfileUpdateSerializer


#1 ListOfAllUsers
class ListOfUsersView(APIView):
    def get(self,request):
        users = User.objects.all()
        serializer = ListOfUsersSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#2 registration
class UserRegisterView(APIView):
    def post(self,request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#3 Login
class UserLoginView(APIView):
    def post(self,request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username = serializer.validated_data['username'],
                password = serializer.validated_data['password']
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access_token': str(refresh.access_token),
                    'refresh': str(refresh),
                },status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"detail": "نام کاربری یا رمز عبور اشتباه است"}, status=status.HTTP_401_UNAUTHORIZED)

#4 ListOfAllPendingUsers
class PendingUsersView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]
    def get(self,request):
        users = User.objects.select_related('role').filter(status="pending")
        serializer = ListOfUsersSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#5 ProfileUpdate
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, partial=False):
        user = request.user
        serializer = ProfileUpdateSerializer(instance=user, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'پروفایل با موفقیت بروزرسانی شد',
                'data': serializer.data
            },status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        return self.update(request, partial=False)

    def patch(self, request):
        return self.update(request, partial=True)
#6 Group List
class ListOfGroupsView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]
    def get(self,request):
        groups = Group.objects.all()
        serializer = ListOfGroupsSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
#7 Group Create
class GroupRegisterView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]
    def post(self,request):
        serializer = ListOfGroupsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#8 Assign users to group by admin
class AssignUsersGroups(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]

    def post(self,request):
        serializer = UserGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(assigned_by=request.user)
            return Response({
                'message': "کاربر با موفقیت به گروه افزوده شد.",
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#9 Assign a role to users by admin
class AssignUserRoleView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]
    def patch(self,request,pk):
        user = get_object_or_404(User,pk=pk,deleted_at__isnull=True)
        serializer = UserRoleUpdateSerializer(user,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message':"نقش کاربر با موفقیت بروزرسانی شد." ,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#10 ListOfAllRoles
class ListOfRolesView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]
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

    def patch(self, request, pk):
        user = self.get_object(pk)
        serializer = UserStatusUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            update_user = serializer.save()
            return Response({
                "message": f"وضعیت کاربر با موفقیت به {update_user.status} تغییر یافت.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        user = self.get_object(pk)
        user.deleted_at = timezone.now()
        user.status = 'deleted'
        user.save()
        return Response({"message": "کاربر با موفقیت حذف شد."}, status=status.HTTP_204_NO_CONTENT)

#12 Group Detail, Update, Delete
class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, pk):
        return get_object_or_404(Group.objects.select_related('assigned_by'), pk=pk, deleted_at__isnull=True)

    def get(self, request, pk, *args, **kwargs):
        group = self.get_object(pk)
        serializer = GroupSerializer(group)
        return Response(serializer.data)

    def update(self, request, pk, partial=False):
        group = self.get_object(pk)
        serializer = GroupSerializer(group, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, *args, **kwargs):
        return self.update(request, pk, partial=False)

    def patch(self, request, pk, *args, **kwargs):
        return self.update(request, pk, partial=True)

    def delete(self, request, pk, *args, **kwargs):
        group = self.get_object(pk)
        group.deleted_at = timezone.now()
        group.save()
        return Response({'message': 'گروه با موفقیت حذف شد'}, status=status.HTTP_204_NO_CONTENT)
#13 make user active or inactive
class UserActivationView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]
    def patch(self,request,pk):
        user = get_object_or_404(User,pk=pk,deleted_at__isnull=True)
        is_active = request.data.get('is_active')
        if is_active is None:
            return Response(
                {'error': 'فیلد is_active الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = bool(is_active)
        user.save(update_fields=['is_active'])

        return Response({
            'message': 'کاربر فعال شد' if user.is_active else 'کاربر غیرفعال شد',
            'is_active': user.is_active
        },status=status.HTTP_200_OK)


from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserInfoSerializer,
    VerificationProfileSerializer
)
from .models import VerificationProfile

User = get_user_model()


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                'code': 200,
                'message': '注册成功',
                'data': {
                    'id': serializer.instance.id,
                    'username': serializer.instance.username,
                    'email': serializer.instance.email,
                    'role': serializer.instance.role,
                }
            },
            status=status.HTTP_201_CREATED
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return Response({
                'code': 200,
                'message': '登录成功',
                'data': response.data
            })
        return response


class UserInfoView(generics.RetrieveUpdateAPIView):
    serializer_class = UserInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'code': 200,
            'message': '更新成功',
            'data': serializer.data
        })


class UserLogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({
            'code': 200,
            'message': '退出登录成功'
        })


class VerificationProfileView(generics.ListCreateAPIView, generics.UpdateAPIView):
    serializer_class = VerificationProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VerificationProfile.objects.filter(user=self.request.user)

    def get_object(self):
        try:
            return VerificationProfile.objects.get(user=self.request.user)
        except VerificationProfile.DoesNotExist:
            return None

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': None
            })
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is not None:
            return self.update(request, *args, **kwargs)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'code': 200,
            'message': '实名认证提交成功，请等待审核',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance is None:
            return self.create(request, *args, **kwargs)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'code': 200,
            'message': '实名认证更新成功，请等待审核',
            'data': serializer.data
        })

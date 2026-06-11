from rest_framework import generics, status, permissions, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.utils import timezone
from .models import Project, ProjectStatus
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateSerializer,
    ProjectAuditSerializer
)


class IsInitiator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'initiator'


class IsAuditor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'auditor'


class ProjectPublicListView(generics.ListAPIView):
    serializer_class = ProjectListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Project.objects.filter(
            status__in=[ProjectStatus.APPROVED, ProjectStatus.FUNDING, ProjectStatus.COMPLETED]
        )
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class ProjectCreateView(generics.CreateAPIView):
    serializer_class = ProjectCreateSerializer
    permission_classes = [IsAuthenticated, IsInitiator]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail_serializer = ProjectDetailSerializer(serializer.instance)
        return Response({
            'code': 200,
            'message': '项目提交成功，请等待平台审核',
            'data': detail_serializer.data
        }, status=status.HTTP_201_CREATED)


class ProjectDetailView(generics.RetrieveAPIView):
    serializer_class = ProjectDetailSerializer
    permission_classes = [AllowAny]
    queryset = Project.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status in [ProjectStatus.PENDING, ProjectStatus.REJECTED]:
            if not request.user.is_authenticated:
                return Response({
                    'code': 403,
                    'message': '该项目暂未通过审核，无法查看'
                }, status=status.HTTP_403_FORBIDDEN)
            if request.user.role == 'auditor' or request.user == instance.initiator:
                pass
            else:
                return Response({
                    'code': 403,
                    'message': '该项目暂未通过审核，无法查看'
                }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class MyProjectListView(generics.ListAPIView):
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(initiator=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class PendingProjectListView(generics.ListAPIView):
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated, IsAuditor]

    def get_queryset(self):
        status_filter = self.request.query_params.get('status', 'pending')
        if status_filter == 'all':
            return Project.objects.all().order_by('-created_at')
        return Project.objects.filter(status=status_filter).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class ProjectAuditView(generics.GenericAPIView):
    serializer_class = ProjectAuditSerializer
    permission_classes = [IsAuthenticated, IsAuditor]
    queryset = Project.objects.all()

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        if project.status != ProjectStatus.PENDING:
            return Response({
                'code': 400,
                'message': '该项目状态不是待审核，无法进行审核操作'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        if validated_data['status'] == 'approved':
            project.status = ProjectStatus.FUNDING
        else:
            project.status = ProjectStatus.REJECTED
            project.reject_reason = validated_data.get('reject_reason', '')

        project.auditor = request.user
        project.audited_at = timezone.now()
        project.save()

        detail_serializer = ProjectDetailSerializer(project)
        return Response({
            'code': 200,
            'message': f'项目审核已{"通过" if validated_data["status"] == "approved" else "拒绝"}',
            'data': detail_serializer.data
        })

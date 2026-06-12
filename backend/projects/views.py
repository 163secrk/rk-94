from rest_framework import generics, status, permissions, views, parsers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.utils import timezone
from django.db import transaction
from decimal import Decimal, InvalidOperation
from .models import (
    Project, ProjectStatus, Donation, DonationStatus,
    RefundRequest, RefundRequestStatus,
    Expenditure, ExpenditureInvoice, DonationExpenditure,
    DonationCertificate, CertificateType,
    ProjectUpdate, ProjectUpdateImage, ProjectUpdateVideo, UpdateType,
    Notification, NotificationType
)
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateSerializer,
    ProjectAuditSerializer,
    DonationListSerializer,
    DonationDetailSerializer,
    DonationCreateSerializer,
    PaymentCallbackSerializer,
    RefundRequestCreateSerializer,
    RefundRequestReviewSerializer,
    RefundRequestListSerializer,
    RefundPreviewSerializer,
    ExpenditureListSerializer,
    ExpenditureDetailSerializer,
    ExpenditureCreateSerializer,
    ExpenditureInvoiceSerializer,
    ExpenditureInvoiceCreateSerializer,
    DonationExpenditureCreateSerializer,
    DonationExpenditureDetailSerializer,
    DonationTrackingSerializer,
    ProjectExpenditureSummarySerializer,
    DonationCertificateListSerializer,
    DonationCertificateDetailSerializer,
    CertificateVerifySerializer,
    ProjectUpdateListSerializer,
    ProjectUpdateDetailSerializer,
    ProjectUpdateCreateSerializer,
    NotificationSerializer,
    NotificationMarkReadSerializer,
    MySupportedProjectUpdateSerializer
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
            status__in=[ProjectStatus.APPROVED, ProjectStatus.FUNDING, ProjectStatus.EXECUTING, ProjectStatus.COMPLETED]
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


class DonationCreateView(generics.CreateAPIView):
    serializer_class = DonationCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        donation = serializer.save()
        detail_serializer = DonationDetailSerializer(donation)
        return Response({
            'code': 200,
            'message': '捐赠订单创建成功，请完成支付',
            'data': {
                'donation': detail_serializer.data,
                'payment_url': f'/api/donations/{donation.id}/pay/'
            }
        }, status=status.HTTP_201_CREATED)


class MyDonationListView(generics.ListAPIView):
    serializer_class = DonationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Donation.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class DonationDetailView(generics.RetrieveAPIView):
    serializer_class = DonationDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = Donation.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and request.user.role != 'auditor' and request.user.role != 'admin':
            return Response({
                'code': 403,
                'message': '无权查看该捐赠记录'
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class PaymentCallbackView(generics.GenericAPIView):
    serializer_class = PaymentCallbackSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        donation = validated_data['donation']
        callback_status = validated_data['status']
        transaction_id = validated_data.get('transaction_id', '')

        try:
            if callback_status == 'success':
                donation.update_status(DonationStatus.PAID, transaction_id)
                message = '支付成功，感谢您的捐赠'
            else:
                donation.update_status(DonationStatus.FAILED)
                message = '支付失败'

            detail_serializer = DonationDetailSerializer(donation)
            return Response({
                'code': 200,
                'message': message,
                'data': detail_serializer.data
            })
        except ValueError as e:
            return Response({
                'code': 400,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SimulatePaymentView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Donation.objects.all()

    def post(self, request, *args, **kwargs):
        donation = self.get_object()
        if donation.user != request.user:
            return Response({
                'code': 403,
                'message': '无权操作该捐赠订单'
            }, status=status.HTTP_403_FORBIDDEN)

        if donation.status != DonationStatus.PENDING:
            return Response({
                'code': 400,
                'message': '该订单已处理，无法重复支付'
            }, status=status.HTTP_400_BAD_REQUEST)

        import random
        success = random.choice([True, True, True, False])
        transaction_id = f'TXN{timezone.now().strftime("%Y%m%d%H%M%S")}{random.randint(100000, 999999)}'

        try:
            if success:
                donation.update_status(DonationStatus.PAID, transaction_id)
                message = '模拟支付成功，感谢您的捐赠'
            else:
                donation.update_status(DonationStatus.FAILED)
                message = '模拟支付失败'

            detail_serializer = DonationDetailSerializer(donation)
            return Response({
                'code': 200,
                'message': message,
                'data': detail_serializer.data
            })
        except ValueError as e:
            return Response({
                'code': 400,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class DonationRefundView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAuditor]
    queryset = Donation.objects.all()

    def post(self, request, *args, **kwargs):
        donation = self.get_object()
        refund_transaction_id = request.data.get('refund_transaction_id')
        try:
            donation.refund(refund_transaction_id)
            detail_serializer = DonationDetailSerializer(donation)
            return Response({
                'code': 200,
                'message': '退款成功',
                'data': detail_serializer.data
            })
        except ValueError as e:
            return Response({
                'code': 400,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class DonationRefundPreviewView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Donation.objects.all()

    def get(self, request, *args, **kwargs):
        donation = self.get_object()
        if donation.user != request.user and request.user.role != 'auditor' and request.user.role != 'admin':
            return Response({
                'code': 403,
                'message': '无权查看该捐赠的退款信息'
            }, status=status.HTTP_403_FORBIDDEN)

        preview_data = donation.calculate_refund_preview()
        serializer = RefundPreviewSerializer(preview_data)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class RefundRequestCreateView(generics.CreateAPIView):
    serializer_class = RefundRequestCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund_request = serializer.save(user=request.user)
        detail_serializer = RefundRequestListSerializer(refund_request)
        return Response({
            'code': 200,
            'message': '退款申请提交成功，请等待审核',
            'data': detail_serializer.data
        }, status=status.HTTP_201_CREATED)


class MyRefundRequestListView(generics.ListAPIView):
    serializer_class = RefundRequestListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RefundRequest.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class RefundRequestListView(generics.ListAPIView):
    serializer_class = RefundRequestListSerializer
    permission_classes = [IsAuthenticated, IsAuditor]

    def get_queryset(self):
        return RefundRequest.objects.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status', 'pending')
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class RefundRequestReviewView(generics.GenericAPIView):
    serializer_class = RefundRequestReviewSerializer
    permission_classes = [IsAuthenticated, IsAuditor]
    queryset = RefundRequest.objects.all()

    def post(self, request, *args, **kwargs):
        refund_request = self.get_object()
        if refund_request.status != RefundRequestStatus.PENDING:
            return Response({
                'code': 400,
                'message': '该申请已处理，无法重复审核'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            action = validated_data['action']
            if action == 'approve':
                refund_transaction_id = request.data.get('refund_transaction_id')
                refund_request.approve(request.user, refund_transaction_id)
                message = '退款申请已通过，退款已完成'
            else:
                refund_request.reject(request.user, validated_data.get('review_reason', ''))
                message = '退款申请已拒绝'

            detail_serializer = RefundRequestListSerializer(refund_request)
            return Response({
                'code': 200,
                'message': message,
                'data': detail_serializer.data
            })
        except ValueError as e:
            return Response({
                'code': 400,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ProjectStartView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAuditor]
    queryset = Project.objects.all()

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        if project.status != ProjectStatus.FUNDING:
            return Response({
                'code': 400,
                'message': '只有募集中的项目可以开始执行'
            }, status=status.HTTP_400_BAD_REQUEST)

        if project.current_amount <= 0:
            return Response({
                'code': 400,
                'message': '项目尚无筹款，无法开始执行'
            }, status=status.HTTP_400_BAD_REQUEST)

        project.status = ProjectStatus.EXECUTING
        project.start_date = timezone.now().date()
        project.save()

        detail_serializer = ProjectDetailSerializer(project)
        return Response({
            'code': 200,
            'message': '项目已进入执行期',
            'data': detail_serializer.data
        })


class ProjectUpdateUsedAmountView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAuditor]
    queryset = Project.objects.all()

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        if project.status != ProjectStatus.EXECUTING:
            return Response({
                'code': 400,
                'message': '只有执行中的项目可以更新已使用金额'
            }, status=status.HTTP_400_BAD_REQUEST)

        used_amount = request.data.get('used_amount')
        if used_amount is None:
            return Response({
                'code': 400,
                'message': '请提供已使用金额'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            used_amount = Decimal(str(used_amount))
        except (ValueError, InvalidOperation):
            return Response({
                'code': 400,
                'message': '已使用金额格式不正确'
            }, status=status.HTTP_400_BAD_REQUEST)

        if used_amount < 0:
            return Response({
                'code': 400,
                'message': '已使用金额不能为负数'
            }, status=status.HTTP_400_BAD_REQUEST)

        if used_amount > project.current_amount:
            return Response({
                'code': 400,
                'message': '已使用金额不能超过当前已筹金额'
            }, status=status.HTTP_400_BAD_REQUEST)

        project.used_amount = used_amount
        project.save()

        detail_serializer = ProjectDetailSerializer(project)
        return Response({
            'code': 200,
            'message': '已使用金额更新成功',
            'data': {
                'project': detail_serializer.data,
                'execution_ratio': float(project.execution_ratio * 100)
            }
        })


class ProjectDonationListView(generics.ListAPIView):
    serializer_class = DonationListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Donation.objects.filter(
            project_id=project_id,
            status=DonationStatus.PAID
        ).order_by('-paid_at')

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


class IsAdminOrAuditor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['auditor', 'admin']


class ExpenditureListView(generics.ListAPIView):
    serializer_class = ExpenditureListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        queryset = Expenditure.objects.all()
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if not (self.request.user.role in ['auditor', 'admin']):
            queryset = queryset.filter(project__initiator=self.request.user)
        return queryset.order_by('-expenditure_date', '-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        expenditure_type = request.query_params.get('expenditure_type')
        if expenditure_type:
            queryset = queryset.filter(expenditure_type=expenditure_type)
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


class ExpenditureCreateView(generics.CreateAPIView):
    serializer_class = ExpenditureCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAuditor]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expenditure = serializer.save(operator=request.user)
        project = expenditure.project
        project.used_amount = min(
            project.used_amount + expenditure.amount,
            project.current_amount
        )
        project.save()
        detail_serializer = ExpenditureDetailSerializer(expenditure)
        return Response({
            'code': 200,
            'message': '支出记录创建成功',
            'data': detail_serializer.data
        }, status=status.HTTP_201_CREATED)


class ExpenditureDetailView(generics.RetrieveAPIView):
    serializer_class = ExpenditureDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = Expenditure.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (request.user.role in ['auditor', 'admin']) and instance.project.initiator != request.user:
            return Response({
                'code': 403,
                'message': '无权查看该支出记录'
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class ExpenditureInvoiceUploadView(generics.CreateAPIView):
    serializer_class = ExpenditureInvoiceCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAuditor]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def create(self, request, *args, **kwargs):
        expenditure_id = self.kwargs.get('expenditure_id')
        try:
            expenditure = Expenditure.objects.get(id=expenditure_id)
        except Expenditure.DoesNotExist:
            return Response({
                'code': 404,
                'message': '支出记录不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save(
            expenditure=expenditure,
            uploaded_by=request.user
        )
        detail_serializer = ExpenditureInvoiceSerializer(invoice)
        return Response({
            'code': 200,
            'message': '发票上传成功',
            'data': detail_serializer.data
        }, status=status.HTTP_201_CREATED)


class DonationExpenditureAllocateView(generics.CreateAPIView):
    serializer_class = DonationExpenditureCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAuditor]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        allocation = serializer.save(allocated_by=request.user)
        detail_serializer = DonationExpenditureDetailSerializer(allocation)
        return Response({
            'code': 200,
            'message': '捐款分配成功',
            'data': detail_serializer.data
        }, status=status.HTTP_201_CREATED)


class DonationTrackingView(generics.RetrieveAPIView):
    serializer_class = DonationTrackingSerializer
    permission_classes = [IsAuthenticated]
    queryset = Donation.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and request.user.role not in ['auditor', 'admin']:
            return Response({
                'code': 403,
                'message': '无权查看该捐赠记录的追踪信息'
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class ProjectExpenditureSummaryView(generics.RetrieveAPIView):
    serializer_class = ProjectExpenditureSummarySerializer
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (request.user.role in ['auditor', 'admin']) and instance.initiator != request.user:
            return Response({
                'code': 403,
                'message': '无权查看该项目的支出汇总'
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class AvailableDonationsForAllocationView(generics.ListAPIView):
    serializer_class = DonationListSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAuditor]

    def get_queryset(self):
        expenditure_id = self.kwargs.get('expenditure_id')
        try:
            expenditure = Expenditure.objects.get(id=expenditure_id)
        except Expenditure.DoesNotExist:
            return Donation.objects.none()

        allocated_ids = DonationExpenditure.objects.filter(
            expenditure=expenditure
        ).values_list('donation_id', flat=True)

        return Donation.objects.filter(
            project=expenditure.project,
            status=DonationStatus.PAID
        ).exclude(id__in=allocated_ids).order_by('-paid_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class MyCertificateListView(generics.ListAPIView):
    serializer_class = DonationCertificateListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = DonationCertificate.objects.filter(user=self.request.user)
        certificate_type = self.request.query_params.get('certificate_type')
        if certificate_type:
            queryset = queryset.filter(certificate_type=certificate_type)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class CertificateDetailView(generics.RetrieveAPIView):
    serializer_class = DonationCertificateDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = DonationCertificate.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and request.user.role not in ['auditor', 'admin']:
            return Response({
                'code': 403,
                'message': '无权查看该证书'
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class CertificateVerifyView(generics.GenericAPIView):
    serializer_class = CertificateVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        certificate_no = serializer.validated_data['certificate_no']

        try:
            certificate = DonationCertificate.objects.get(certificate_no=certificate_no)
        except DonationCertificate.DoesNotExist:
            return Response({
                'code': 404,
                'message': '证书不存在',
                'data': {'is_valid': False}
            }, status=status.HTTP_404_NOT_FOUND)

        is_valid = certificate.verify_integrity()

        provided_hash = serializer.validated_data.get('integrity_hash')
        hash_matched = True
        if provided_hash:
            import hmac as hmac_mod
            hash_matched = hmac_mod.compare_digest(provided_hash, certificate.integrity_hash)

        detail_serializer = DonationCertificateDetailSerializer(certificate)
        return Response({
            'code': 200,
            'message': '证书验证通过' if is_valid and hash_matched else '证书验证失败，数据可能已被篡改',
            'data': {
                **detail_serializer.data,
                'is_valid': is_valid,
                'hash_matched': hash_matched
            }
        })


class ProjectCertificateListView(generics.ListAPIView):
    serializer_class = DonationCertificateListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return DonationCertificate.objects.filter(project_id=project_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class ProjectUpdateListView(generics.ListAPIView):
    serializer_class = ProjectUpdateListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return ProjectUpdate.objects.filter(project_id=project_id).order_by('-created_at')

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


class ProjectUpdateCreateView(generics.CreateAPIView):
    serializer_class = ProjectUpdateCreateSerializer
    permission_classes = [IsAuthenticated, IsInitiator]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        images = request.FILES.getlist('images')
        videos = request.FILES.getlist('videos')
        if images:
            data.setlist('images', images)
        if videos:
            data.setlist('videos', videos)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        project_update = serializer.save()
        detail_serializer = ProjectUpdateDetailSerializer(project_update)
        return Response({
            'code': 200,
            'message': '项目进展发布成功',
            'data': detail_serializer.data
        }, status=status.HTTP_201_CREATED)


class ProjectUpdateDetailView(generics.RetrieveAPIView):
    serializer_class = ProjectUpdateDetailSerializer
    permission_classes = [AllowAny]
    queryset = ProjectUpdate.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class MyProjectUpdateListView(generics.ListAPIView):
    serializer_class = ProjectUpdateListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        queryset = ProjectUpdate.objects.filter(initiator=self.request.user)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
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


class MySupportedProjectUpdatesView(generics.ListAPIView):
    serializer_class = MySupportedProjectUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        donated_project_ids = Donation.objects.filter(
            user=user,
            status=DonationStatus.PAID
        ).values_list('project_id', flat=True).distinct()

        return ProjectUpdate.objects.filter(
            project_id__in=donated_project_ids
        ).select_related('project', 'initiator').order_by('-created_at')

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


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        is_read = self.request.query_params.get('is_read')
        notification_type = self.request.query_params.get('type')
        if is_read is not None:
            queryset = queryset.filter(is_read=(is_read.lower() == 'true'))
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data)
            unread_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
            data.data['unread_count'] = unread_count
            return data
        serializer = self.get_serializer(queryset, many=True)
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': {
                'list': serializer.data,
                'unread_count': unread_count
            }
        })


class NotificationUnreadCountView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': {
                'unread_count': count
            }
        })


class NotificationMarkReadView(generics.GenericAPIView):
    serializer_class = NotificationMarkReadSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        queryset = Notification.objects.filter(user=request.user)

        if validated_data.get('all'):
            updated = queryset.filter(is_read=False).update(
                is_read=True,
                read_at=timezone.now()
            )
        else:
            notification_ids = validated_data.get('notification_ids', [])
            if not notification_ids:
                return Response({
                    'code': 400,
                    'message': '请选择要标记为已读的通知'
                }, status=status.HTTP_400_BAD_REQUEST)
            updated = queryset.filter(
                id__in=notification_ids,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )

        return Response({
            'code': 200,
            'message': f'已标记 {updated} 条通知为已读',
            'data': {
                'updated_count': updated
            }
        })


class NotificationDetailView(generics.RetrieveAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({
                'code': 403,
                'message': '无权查看该通知'
            }, status=status.HTTP_403_FORBIDDEN)

        if not instance.is_read:
            instance.mark_as_read()

        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })

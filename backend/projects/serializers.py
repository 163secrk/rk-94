from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import models as db_models
from django.db import transaction
from decimal import Decimal
import json
from .models import (
    Project, ProjectBudget, ProjectStatus, ProjectCategory,
    Donation, DonationStatus, RefundRequest, RefundRequestStatus,
    Expenditure, ExpenditureInvoice, DonationExpenditure, ExpenditureType,
    DonationCertificate, CertificateType,
    ProjectUpdate, ProjectUpdateImage, ProjectUpdateVideo, UpdateType,
    Notification, NotificationType
)

User = get_user_model()


class ProjectBudgetSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = ProjectBudget
        fields = ['id', 'category', 'description', 'amount', 'quantity', 'unit', 'subtotal']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('预算金额必须大于0')
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('数量必须大于0')
        return value


class ProjectBudgetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectBudget
        fields = ['category', 'description', 'amount', 'quantity', 'unit']


class InitiatorInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar']


class ProjectListSerializer(serializers.ModelSerializer):
    initiator = InitiatorInfoSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    execution_ratio = serializers.DecimalField(max_digits=6, decimal_places=4, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'category', 'category_display', 'description',
            'cover_image', 'target_amount', 'current_amount', 'used_amount',
            'progress_percentage', 'execution_ratio',
            'start_date', 'deadline', 'status', 'status_display', 'initiator', 'created_at'
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    initiator = InitiatorInfoSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    budgets = ProjectBudgetSerializer(many=True, read_only=True)
    budget_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    execution_ratio = serializers.DecimalField(max_digits=6, decimal_places=4, read_only=True)
    is_refundable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'category', 'category_display', 'description', 'detail_content',
            'cover_image', 'target_amount', 'current_amount', 'used_amount', 'progress_percentage',
            'execution_ratio', 'is_refundable', 'start_date', 'deadline',
            'status', 'status_display', 'reject_reason',
            'initiator', 'budgets', 'budget_total', 'audited_at', 'created_at', 'updated_at'
        ]


class BudgetsJsonField(serializers.Field):
    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
            except (json.JSONDecodeError, ValueError):
                raise serializers.ValidationError('值必须是有效的 JSON 数据。')
            data = parsed
        if not isinstance(data, list):
            raise serializers.ValidationError('预算数据必须是数组格式。')
        return data

    def to_representation(self, value):
        return value


class ProjectCreateSerializer(serializers.ModelSerializer):
    budgets = BudgetsJsonField(required=True, write_only=True)

    class Meta:
        model = Project
        fields = [
            'title', 'category', 'description', 'detail_content',
            'cover_image', 'target_amount', 'deadline', 'budgets'
        ]

    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('目标金额必须大于0')
        return value

    def validate_budgets(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError('至少需要填写一条预算明细')
        return value

    def validate(self, attrs):
        budgets_data = attrs.get('budgets', [])
        total_budget = Decimal('0')
        for budget in budgets_data:
            amount = Decimal(str(budget.get('amount', '0')))
            quantity = int(budget.get('quantity', 1))
            total_budget += amount * quantity

        if total_budget > attrs.get('target_amount', Decimal('0')):
            raise serializers.ValidationError({'budgets': '预算总金额不能超过目标金额'})

        return attrs

    def create(self, validated_data):
        budgets_data = validated_data.pop('budgets')
        user = self.context['request'].user

        if not user.is_verified:
            raise serializers.ValidationError('请先完成实名认证后再发起项目')
        if user.role != 'initiator':
            raise serializers.ValidationError('只有项目发起方角色可以创建公益项目')

        validated_data['initiator'] = user
        validated_data['status'] = ProjectStatus.PENDING
        project = Project.objects.create(**validated_data)

        for budget_data in budgets_data:
            budget_data['amount'] = Decimal(str(budget_data.get('amount', '0')))
            budget_data['quantity'] = int(budget_data.get('quantity', 1))
            ProjectBudget.objects.create(project=project, **budget_data)

        return project


class ProjectAuditSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        ('approved', '通过'),
        ('rejected', '拒绝')
    ])
    reject_reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        if attrs.get('status') == 'rejected' and not attrs.get('reject_reason'):
            raise serializers.ValidationError({'reject_reason': '拒绝时必须填写拒绝原因'})
        return attrs


class DonorInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']


class DonationProjectInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'cover_image']


class DonationListSerializer(serializers.ModelSerializer):
    project = DonationProjectInfoSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Donation
        fields = [
            'id', 'order_no', 'project', 'amount', 'status', 'status_display',
            'message', 'paid_at', 'created_at'
        ]


class DonationDetailSerializer(serializers.ModelSerializer):
    user = DonorInfoSerializer(read_only=True)
    project = DonationProjectInfoSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Donation
        fields = [
            'id', 'order_no', 'user', 'project', 'amount', 'status', 'status_display',
            'message', 'paid_at', 'refunded_at', 'refund_amount', 'platform_fee',
            'execution_ratio_at_refund', 'transaction_id', 'refund_transaction_id',
            'created_at', 'updated_at'
        ]


class DonationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ['project', 'amount', 'message']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('捐赠金额必须大于0')
        return value

    def validate_project(self, value):
        if value.status not in [ProjectStatus.FUNDING, ProjectStatus.APPROVED]:
            raise serializers.ValidationError('该项目当前无法接受捐赠')
        return value

    def create(self, validated_data):
        import uuid
        from django.utils import timezone

        user = self.context['request'].user
        if not user.is_authenticated:
            raise serializers.ValidationError('请先登录后再进行捐赠')

        order_no = f'DON{timezone.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:8].upper()}'

        donation = Donation.objects.create(
            order_no=order_no,
            user=user,
            **validated_data
        )
        return donation


class PaymentCallbackSerializer(serializers.Serializer):
    order_no = serializers.CharField(max_length=32, required=True)
    status = serializers.ChoiceField(choices=[('success', '支付成功'), ('failed', '支付失败')], required=True)
    transaction_id = serializers.CharField(max_length=64, required=False, allow_blank=True)

    def validate(self, attrs):
        try:
            donation = Donation.objects.get(order_no=attrs['order_no'])
        except Donation.DoesNotExist:
            raise serializers.ValidationError({'order_no': '订单不存在'})

        if donation.status != DonationStatus.PENDING:
            raise serializers.ValidationError({'order_no': '该订单已处理，无法重复回调'})

        attrs['donation'] = donation
        return attrs


class RefundRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = ['donation', 'reason']

    def validate_donation(self, value):
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError('只能申请退还自己的捐赠')
        if value.status != DonationStatus.PAID:
            raise serializers.ValidationError('该捐赠状态不支持退款')
        if not value.project.is_refundable:
            raise serializers.ValidationError('该项目不支持退款')
        if hasattr(value, 'refund_request') and value.refund_request:
            if value.refund_request.status == RefundRequestStatus.PENDING:
                raise serializers.ValidationError('该捐赠已有退款申请待审核')
            if value.refund_request.status == RefundRequestStatus.APPROVED:
                raise serializers.ValidationError('该捐赠已完成退款')
        preview = value.calculate_refund_preview()
        if not preview.get('can_refund'):
            raise serializers.ValidationError(preview.get('reason', '该捐赠不支持退款'))
        return value


class RefundRequestReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=[('approve', '通过'), ('reject', '拒绝')])
    review_reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        if attrs.get('action') == 'reject' and not attrs.get('review_reason'):
            raise serializers.ValidationError({'review_reason': '拒绝时必须填写审核意见'})
        return attrs


class RefundRequestListSerializer(serializers.ModelSerializer):
    donation = DonationDetailSerializer(read_only=True)
    user = DonorInfoSerializer(read_only=True)
    reviewer = DonorInfoSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RefundRequest
        fields = [
            'id', 'donation', 'user', 'reason', 'status', 'status_display',
            'review_reason', 'reviewer', 'reviewed_at', 'created_at', 'updated_at'
        ]


class RefundPreviewSerializer(serializers.Serializer):
    can_refund = serializers.BooleanField()
    reason = serializers.CharField(required=False, allow_null=True)
    donation_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    refundable_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    platform_fee = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    platform_fee_rate = serializers.CharField(required=False)
    actual_refund = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    execution_ratio = serializers.DecimalField(max_digits=6, decimal_places=4, required=False)
    project_status = serializers.CharField(required=False)


class ExpenditureInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenditureInvoice
        fields = ['id', 'invoice_no', 'invoice_file', 'amount', 'issued_date', 'issuer', 'remark', 'created_at']
        read_only_fields = ['id', 'created_at']


class ExpenditureInvoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenditureInvoice
        fields = ['invoice_no', 'invoice_file', 'amount', 'issued_date', 'issuer', 'remark']


class DonationAllocationInfoSerializer(serializers.ModelSerializer):
    donation_order_no = serializers.CharField(source='donation.order_no', read_only=True)
    donor_username = serializers.CharField(source='donation.user.username', read_only=True)
    donor_avatar = serializers.CharField(source='donation.user.avatar', read_only=True, allow_null=True)
    donation_amount = serializers.DecimalField(source='donation.amount', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = DonationExpenditure
        fields = ['id', 'donation_order_no', 'donor_username', 'donor_avatar', 'donation_amount', 'amount', 'created_at']
        read_only_fields = ['id', 'created_at']


class ExpenditureListSerializer(serializers.ModelSerializer):
    expenditure_type_display = serializers.CharField(source='get_expenditure_type_display', read_only=True)
    allocated_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    invoices_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True, allow_null=True)

    class Meta:
        model = Expenditure
        fields = [
            'id', 'project', 'project_title', 'expenditure_type', 'expenditure_type_display',
            'title', 'description', 'amount', 'allocated_amount', 'invoices_total',
            'expenditure_date', 'recipient', 'operator_name', 'remark', 'created_at', 'updated_at'
        ]


class ExpenditureDetailSerializer(serializers.ModelSerializer):
    expenditure_type_display = serializers.CharField(source='get_expenditure_type_display', read_only=True)
    allocated_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    invoices_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True, allow_null=True)
    invoices = ExpenditureInvoiceSerializer(many=True, read_only=True)
    donation_allocations = DonationAllocationInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Expenditure
        fields = [
            'id', 'project', 'project_title', 'expenditure_type', 'expenditure_type_display',
            'title', 'description', 'amount', 'allocated_amount', 'invoices_total',
            'expenditure_date', 'recipient', 'operator_name', 'remark',
            'invoices', 'donation_allocations', 'created_at', 'updated_at'
        ]


class ExpenditureCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenditure
        fields = [
            'project', 'expenditure_type', 'title', 'description',
            'amount', 'expenditure_date', 'recipient', 'remark'
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('支出金额必须大于0')
        return value

    def validate_project(self, value):
        if value.status not in [ProjectStatus.EXECUTING, ProjectStatus.COMPLETED]:
            raise serializers.ValidationError('只有执行中或已完成的项目才能登记支出')
        return value


class DonationExpenditureCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationExpenditure
        fields = ['donation', 'expenditure', 'amount']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('分配金额必须大于0')
        return value

    def validate(self, attrs):
        donation = attrs.get('donation')
        expenditure = attrs.get('expenditure')
        amount = attrs.get('amount')

        if donation.project_id != expenditure.project_id:
            raise serializers.ValidationError('捐赠和支出必须属于同一个项目')

        if donation.status != DonationStatus.PAID:
            raise serializers.ValidationError('只有已支付的捐赠才能进行分配')

        total_allocated = DonationExpenditure.objects.filter(donation=donation).aggregate(
            total=db_models.Sum('amount')
        )['total'] or Decimal('0')

        if self.instance:
            total_allocated -= self.instance.amount

        if total_allocated + amount > donation.amount:
            raise serializers.ValidationError({'amount': '分配金额超出该捐赠的剩余可分配金额'})

        return attrs


class DonationExpenditureDetailSerializer(serializers.ModelSerializer):
    donation_order_no = serializers.CharField(source='donation.order_no', read_only=True)
    donor_username = serializers.CharField(source='donation.user.username', read_only=True)
    expenditure_id = serializers.IntegerField(source='expenditure.id', read_only=True)
    expenditure_title = serializers.CharField(source='expenditure.title', read_only=True)
    expenditure_type = serializers.CharField(source='expenditure.expenditure_type', read_only=True)
    expenditure_type_display = serializers.CharField(source='expenditure.get_expenditure_type_display', read_only=True)
    project_title = serializers.CharField(source='expenditure.project.title', read_only=True)
    allocated_by_name = serializers.CharField(source='allocated_by.username', read_only=True, allow_null=True)

    class Meta:
        model = DonationExpenditure
        fields = [
            'id', 'donation_order_no', 'donor_username', 'expenditure_id', 'expenditure_title',
            'expenditure_type', 'expenditure_type_display', 'project_title',
            'amount', 'allocated_by_name', 'created_at'
        ]


class DonationTrackingSerializer(serializers.ModelSerializer):
    expenditure_allocations = DonationExpenditureDetailSerializer(many=True, read_only=True, source='expenditure_allocations')
    total_allocated = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Donation
        fields = [
            'id', 'order_no', 'amount', 'status', 'status_display',
            'total_allocated', 'expenditure_allocations', 'paid_at', 'created_at'
        ]

    def get_total_allocated(self, obj):
        return obj.expenditure_allocations.aggregate(
            total=db_models.Sum('amount')
        )['total'] or Decimal('0')


class ProjectExpenditureSummarySerializer(serializers.ModelSerializer):
    expenditures = ExpenditureListSerializer(many=True, read_only=True)
    total_expenditure = serializers.SerializerMethodField()
    total_allocated = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'current_amount', 'used_amount',
            'total_expenditure', 'total_allocated', 'expenditures'
        ]

    def get_total_expenditure(self, obj):
        return obj.expenditures.aggregate(total=db_models.Sum('amount'))['total'] or Decimal('0')

    def get_total_allocated(self, obj):
        return DonationExpenditure.objects.filter(
            expenditure__project=obj
        ).aggregate(total=db_models.Sum('amount'))['total'] or Decimal('0')


class CertificateProjectInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'category', 'cover_image']


class DonationCertificateListSerializer(serializers.ModelSerializer):
    certificate_type_display = serializers.CharField(source='get_certificate_type_display', read_only=True)
    project = CertificateProjectInfoSerializer(read_only=True)

    class Meta:
        model = DonationCertificate
        fields = [
            'id', 'certificate_no', 'certificate_type', 'certificate_type_display',
            'donation_amount', 'project', 'issued_at'
        ]


class DonationCertificateDetailSerializer(serializers.ModelSerializer):
    certificate_type_display = serializers.CharField(source='get_certificate_type_display', read_only=True)
    project = CertificateProjectInfoSerializer(read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = DonationCertificate
        fields = [
            'id', 'certificate_no', 'certificate_type', 'certificate_type_display',
            'donation_amount', 'project', 'integrity_hash', 'is_valid', 'issued_at'
        ]

    def get_is_valid(self, obj):
        return obj.verify_integrity()


class CertificateVerifySerializer(serializers.Serializer):
    certificate_no = serializers.CharField(max_length=64)
    integrity_hash = serializers.CharField(max_length=128, required=False)


class ProjectUpdateImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdateImage
        fields = ['id', 'image', 'description', 'sort_order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProjectUpdateImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdateImage
        fields = ['image', 'description', 'sort_order']


class ProjectUpdateVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdateVideo
        fields = ['id', 'video', 'cover_image', 'description', 'sort_order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProjectUpdateVideoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdateVideo
        fields = ['video', 'cover_image', 'description', 'sort_order']


class ProjectUpdateSimpleProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'cover_image', 'status', 'status_display']
        read_only_fields = fields

    status_display = serializers.CharField(source='get_status_display', read_only=True)


class ProjectUpdateListSerializer(serializers.ModelSerializer):
    initiator = InitiatorInfoSerializer(read_only=True)
    update_type_display = serializers.CharField(source='get_update_type_display', read_only=True)
    images_count = serializers.SerializerMethodField()
    videos_count = serializers.SerializerMethodField()
    project = ProjectUpdateSimpleProjectSerializer(read_only=True)

    class Meta:
        model = ProjectUpdate
        fields = [
            'id', 'project', 'title', 'content', 'update_type', 'update_type_display',
            'initiator', 'images_count', 'videos_count', 'created_at', 'updated_at'
        ]

    def get_images_count(self, obj):
        return obj.images.count()

    def get_videos_count(self, obj):
        return obj.videos.count()


class ProjectUpdateDetailSerializer(serializers.ModelSerializer):
    initiator = InitiatorInfoSerializer(read_only=True)
    update_type_display = serializers.CharField(source='get_update_type_display', read_only=True)
    images = ProjectUpdateImageSerializer(many=True, read_only=True)
    videos = ProjectUpdateVideoSerializer(many=True, read_only=True)
    project = ProjectUpdateSimpleProjectSerializer(read_only=True)

    class Meta:
        model = ProjectUpdate
        fields = [
            'id', 'project', 'title', 'content', 'update_type', 'update_type_display',
            'initiator', 'images', 'videos', 'created_at', 'updated_at'
        ]


class ProjectUpdateCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    videos = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = ProjectUpdate
        fields = ['project', 'title', 'content', 'images', 'videos']

    def validate_project(self, value):
        user = self.context['request'].user
        if value.initiator != user:
            raise serializers.ValidationError('只能为您自己发起的项目发布进展')
        if value.status not in [ProjectStatus.FUNDING, ProjectStatus.EXECUTING, ProjectStatus.COMPLETED]:
            raise serializers.ValidationError('当前项目状态不允许发布进展')
        return value

    def validate(self, attrs):
        content = attrs.get('content', '')
        images = attrs.get('images', [])
        videos = attrs.get('videos', [])
        if not content.strip() and not images and not videos:
            raise serializers.ValidationError('至少需要填写文字内容或上传图片/视频')
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        videos_data = validated_data.pop('videos', [])
        user = self.context['request'].user
        validated_data['initiator'] = user
        project_update = ProjectUpdate.objects.create(**validated_data)

        for idx, image_file in enumerate(images_data):
            ProjectUpdateImage.objects.create(
                project_update=project_update,
                image=image_file,
                sort_order=idx
            )

        for idx, video_file in enumerate(videos_data):
            ProjectUpdateVideo.objects.create(
                project_update=project_update,
                video=video_file,
                sort_order=idx
            )

        project_update.save()
        project_update.notify_donors()
        return project_update


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'title', 'content', 'is_read', 'read_at',
            'related_project_id', 'related_update_id', 'related_donation_id',
            'created_at'
        ]
        read_only_fields = fields


class NotificationMarkReadSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    all = serializers.BooleanField(required=False, default=False)


class MySupportedProjectUpdateSerializer(serializers.ModelSerializer):
    update_type_display = serializers.CharField(source='get_update_type_display', read_only=True)
    images_count = serializers.SerializerMethodField()
    videos_count = serializers.SerializerMethodField()
    project = ProjectUpdateSimpleProjectSerializer(read_only=True)
    initiator = InitiatorInfoSerializer(read_only=True)

    class Meta:
        model = ProjectUpdate
        fields = [
            'id', 'project', 'title', 'content', 'update_type', 'update_type_display',
            'initiator', 'images_count', 'videos_count', 'created_at'
        ]

    def get_images_count(self, obj):
        return obj.images.count()

    def get_videos_count(self, obj):
        return obj.videos.count()

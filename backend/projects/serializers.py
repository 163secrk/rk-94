from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
from .models import Project, ProjectBudget, ProjectStatus, ProjectCategory, Donation, DonationStatus

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

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'category', 'category_display', 'description',
            'cover_image', 'target_amount', 'current_amount', 'progress_percentage',
            'deadline', 'status', 'status_display', 'initiator', 'created_at'
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    initiator = InitiatorInfoSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    budgets = ProjectBudgetSerializer(many=True, read_only=True)
    budget_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'category', 'category_display', 'description', 'detail_content',
            'cover_image', 'target_amount', 'current_amount', 'progress_percentage',
            'deadline', 'status', 'status_display', 'reject_reason',
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
            'message', 'paid_at', 'refunded_at', 'transaction_id', 'created_at', 'updated_at'
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

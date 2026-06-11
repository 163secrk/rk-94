from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal

User = get_user_model()


class ProjectStatus(models.TextChoices):
    PENDING = 'pending', _('待审核')
    APPROVED = 'approved', _('已通过')
    REJECTED = 'rejected', _('已拒绝')
    FUNDING = 'funding', _('募集中')
    EXECUTING = 'executing', _('执行中')
    COMPLETED = 'completed', _('已完成')


class RefundRequestStatus(models.TextChoices):
    PENDING = 'pending', _('待审核')
    APPROVED = 'approved', _('已通过')
    REJECTED = 'rejected', _('已拒绝')


class ProjectCategory(models.TextChoices):
    EDUCATION = 'education', _('教育助学')
    MEDICAL = 'medical', _('医疗救助')
    DISASTER = 'disaster', _('灾害救援')
    POVERTY = 'poverty', _('扶贫济困')
    ENVIRONMENT = 'environment', _('环境保护')
    ANIMAL = 'animal', _('动物保护')
    ELDERLY = 'elderly', _('关爱老人')
    CHILDREN = 'children', _('关爱儿童')
    OTHER = 'other', _('其他公益')


class DonationStatus(models.TextChoices):
    PENDING = 'pending', _('待支付')
    PAID = 'paid', _('已支付')
    FAILED = 'failed', _('支付失败')
    REFUNDED = 'refunded', _('已退款')


class Project(models.Model):
    initiator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name='项目发起方'
    )
    title = models.CharField(max_length=200, verbose_name='项目标题')
    category = models.CharField(
        max_length=50,
        choices=ProjectCategory.choices,
        default=ProjectCategory.OTHER,
        verbose_name='项目分类'
    )
    description = models.TextField(verbose_name='项目简介')
    detail_content = models.TextField(blank=True, null=True, verbose_name='详细内容')
    cover_image = models.ImageField(upload_to='projects/covers/', blank=True, null=True, verbose_name='封面图片')
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='目标金额（元）')
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='已筹金额（元）')
    used_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='已使用金额（元）')
    start_date = models.DateField(blank=True, null=True, verbose_name='项目开始日期')
    deadline = models.DateField(verbose_name='截止日期')
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PENDING,
        verbose_name='项目状态'
    )
    reject_reason = models.TextField(blank=True, null=True, verbose_name='拒绝原因')
    auditor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='audited_projects',
        verbose_name='审核员'
    )
    audited_at = models.DateTimeField(blank=True, null=True, verbose_name='审核时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '公益项目'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.get_status_display()}'

    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 0
        return round((float(self.current_amount) / float(self.target_amount)) * 100, 2)

    @property
    def budget_total(self):
        return self.budgets.aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def execution_ratio(self):
        if self.current_amount <= 0:
            return Decimal('0')
        return round(self.used_amount / self.current_amount, 4)

    @property
    def is_refundable(self):
        return self.status in [ProjectStatus.FUNDING, ProjectStatus.APPROVED, ProjectStatus.EXECUTING]

    def get_refundable_amount(self, donation_amount):
        if self.status in [ProjectStatus.FUNDING, ProjectStatus.APPROVED]:
            return donation_amount
        elif self.status == ProjectStatus.EXECUTING:
            ratio = self.execution_ratio
            if ratio >= 1:
                return Decimal('0')
            return round(donation_amount * (1 - ratio), 2)
        return Decimal('0')


class ProjectBudget(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name='所属项目'
    )
    category = models.CharField(max_length=100, verbose_name='资金用途分类')
    description = models.TextField(blank=True, null=True, verbose_name='用途说明')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='预算金额（元）')
    quantity = models.IntegerField(default=1, verbose_name='数量')
    unit = models.CharField(max_length=20, blank=True, null=True, verbose_name='单位')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '项目预算明细'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return f'{self.project.title} - {self.category}'

    @property
    def subtotal(self):
        return self.amount * self.quantity


class Donation(models.Model):
    STATUS_TRANSITIONS = {
        DonationStatus.PENDING: [DonationStatus.PAID, DonationStatus.FAILED],
        DonationStatus.PAID: [DonationStatus.REFUNDED],
        DonationStatus.FAILED: [],
        DonationStatus.REFUNDED: [],
    }

    order_no = models.CharField(max_length=32, unique=True, verbose_name='订单号')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='donations',
        verbose_name='捐赠人'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='donations',
        verbose_name='所属项目'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='捐赠金额（元）')
    status = models.CharField(
        max_length=20,
        choices=DonationStatus.choices,
        default=DonationStatus.PENDING,
        verbose_name='捐赠状态'
    )
    message = models.CharField(max_length=500, blank=True, null=True, verbose_name='留言')
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name='支付时间')
    refunded_at = models.DateTimeField(blank=True, null=True, verbose_name='退款时间')
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='退款金额（元）')
    platform_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='平台维护费（元）')
    execution_ratio_at_refund = models.DecimalField(max_digits=6, decimal_places=4, default=0.0000, verbose_name='退款时执行比例')
    transaction_id = models.CharField(max_length=64, blank=True, null=True, verbose_name='交易流水号')
    refund_transaction_id = models.CharField(max_length=64, blank=True, null=True, verbose_name='退款交易流水号')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '捐赠记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_no} - {self.user.username} - {self.amount}元'

    def can_transition_to(self, new_status):
        return new_status in self.STATUS_TRANSITIONS.get(self.status, [])

    @transaction.atomic
    def update_status(self, new_status, transaction_id=None):
        from django.utils import timezone

        if not self.can_transition_to(new_status):
            raise ValueError(
                f'无法从状态 {self.get_status_display()} 转换到 {dict(DonationStatus.choices)[new_status]}'
            )

        old_status = self.status
        self.status = new_status

        if new_status == DonationStatus.PAID:
            self.paid_at = timezone.now()
            if transaction_id:
                self.transaction_id = transaction_id
            self._update_project_amount(self.amount)
        elif new_status == DonationStatus.REFUNDED:
            self.refunded_at = timezone.now()
            if old_status == DonationStatus.PAID:
                self._update_project_amount(-self.amount)

        self.save()
        return self

    def _update_project_amount(self, delta):
        project = Project.objects.select_for_update().get(pk=self.project_id)
        project.current_amount = models.F('current_amount') + delta
        project.save()
        project.refresh_from_db()

        if project.current_amount >= project.target_amount and project.status == ProjectStatus.FUNDING:
            project.status = ProjectStatus.COMPLETED
            project.save()

    @transaction.atomic
    def refund(self, refund_transaction_id=None):
        from django.utils import timezone

        PLATFORM_FEE_RATE = Decimal('0.006')

        if not self.can_transition_to(DonationStatus.REFUNDED):
            raise ValueError(
                f'无法从状态 {self.get_status_display()} 转换到 {dict(DonationStatus.choices)[DonationStatus.REFUNDED]}'
            )

        project = Project.objects.select_for_update().get(pk=self.project_id)

        if not project.is_refundable:
            raise ValueError(f'项目状态为 {project.get_status_display()}，不支持退款')

        refundable_amount = project.get_refundable_amount(self.amount)
        if refundable_amount <= 0:
            raise ValueError('该捐赠无可退余额')

        platform_fee = round(refundable_amount * PLATFORM_FEE_RATE, 2)
        actual_refund = round(refundable_amount - platform_fee, 2)

        if actual_refund <= 0:
            raise ValueError('扣除平台维护费后退款金额为0，无法退款')

        old_status = self.status
        self.status = DonationStatus.REFUNDED
        self.refunded_at = timezone.now()
        self.refund_amount = actual_refund
        self.platform_fee = platform_fee
        self.execution_ratio_at_refund = project.execution_ratio
        if refund_transaction_id:
            self.refund_transaction_id = refund_transaction_id

        if old_status == DonationStatus.PAID:
            project.current_amount = models.F('current_amount') - self.amount
            if project.status == ProjectStatus.EXECUTING and project.used_amount > 0:
                amount_to_reduce = self.amount * project.execution_ratio
                project.used_amount = models.F('used_amount') - amount_to_reduce
            project.save()
            project.refresh_from_db()

            if project.current_amount < project.target_amount and project.status == ProjectStatus.COMPLETED:
                project.status = ProjectStatus.FUNDING
                project.save()

        self.save()
        return self

    def calculate_refund_preview(self):
        PLATFORM_FEE_RATE = Decimal('0.006')
        project = self.project

        if not project.is_refundable or self.status != DonationStatus.PAID:
            return {
                'can_refund': False,
                'reason': '该捐赠不支持退款' if self.status != DonationStatus.PAID else f'项目状态为 {project.get_status_display()}，不支持退款'
            }

        refundable_amount = project.get_refundable_amount(self.amount)
        if refundable_amount <= 0:
            return {
                'can_refund': False,
                'reason': '该捐赠无可退余额'
            }

        platform_fee = round(refundable_amount * PLATFORM_FEE_RATE, 2)
        actual_refund = round(refundable_amount - platform_fee, 2)

        return {
            'can_refund': actual_refund > 0,
            'donation_amount': self.amount,
            'refundable_amount': refundable_amount,
            'platform_fee': platform_fee,
            'platform_fee_rate': f'{PLATFORM_FEE_RATE * 100}%',
            'actual_refund': actual_refund,
            'execution_ratio': project.execution_ratio,
            'project_status': project.get_status_display()
        }


class ExpenditureType(models.TextChoices):
    MATERIAL = 'material', _('物料采购')
    CASH = 'cash', _('现金发放')
    SERVICE = 'service', _('服务采购')
    OTHER = 'other', _('其他支出')


class Expenditure(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='expenditures',
        verbose_name='所属项目'
    )
    expenditure_type = models.CharField(
        max_length=20,
        choices=ExpenditureType.choices,
        default=ExpenditureType.OTHER,
        verbose_name='支出类型'
    )
    title = models.CharField(max_length=200, verbose_name='支出标题')
    description = models.TextField(verbose_name='支出说明')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='支出金额（元）')
    expenditure_date = models.DateField(verbose_name='支出日期')
    recipient = models.CharField(max_length=200, verbose_name='收款方/接收人')
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operated_expenditures',
        verbose_name='经办人'
    )
    remark = models.TextField(blank=True, null=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '支出记录'
        verbose_name_plural = verbose_name
        ordering = ['-expenditure_date', '-created_at']

    def __str__(self):
        return f'{self.project.title} - {self.title} - {self.amount}元'

    @property
    def allocated_amount(self):
        return self.donation_allocations.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

    @property
    def invoices_total(self):
        return self.invoices.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')


class ExpenditureInvoice(models.Model):
    expenditure = models.ForeignKey(
        Expenditure,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='所属支出'
    )
    invoice_no = models.CharField(max_length=100, blank=True, null=True, verbose_name='发票号码')
    invoice_file = models.FileField(upload_to='invoices/', verbose_name='发票文件')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='发票金额（元）')
    issued_date = models.DateField(blank=True, null=True, verbose_name='开票日期')
    issuer = models.CharField(max_length=200, blank=True, null=True, verbose_name='开票方')
    remark = models.TextField(blank=True, null=True, verbose_name='备注')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_invoices',
        verbose_name='上传人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '支出发票'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.expenditure.title} - 发票 - {self.amount}元'


class DonationExpenditure(models.Model):
    donation = models.ForeignKey(
        Donation,
        on_delete=models.CASCADE,
        related_name='expenditure_allocations',
        verbose_name='关联捐赠'
    )
    expenditure = models.ForeignKey(
        Expenditure,
        on_delete=models.CASCADE,
        related_name='donation_allocations',
        verbose_name='关联支出'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='分配金额（元）')
    allocated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allocated_donations',
        verbose_name='分配人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '捐款支出分配'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        unique_together = [['donation', 'expenditure']]

    def __str__(self):
        return f'{self.donation.order_no} -> {self.expenditure.title} ({self.amount}元)'


class RefundRequest(models.Model):
    donation = models.OneToOneField(
        Donation,
        on_delete=models.CASCADE,
        related_name='refund_request',
        verbose_name='关联捐赠'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='refund_requests',
        verbose_name='申请人'
    )
    reason = models.TextField(max_length=1000, verbose_name='退款原因')
    status = models.CharField(
        max_length=20,
        choices=RefundRequestStatus.choices,
        default=RefundRequestStatus.PENDING,
        verbose_name='申请状态'
    )
    review_reason = models.TextField(max_length=1000, blank=True, null=True, verbose_name='审核意见')
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reviewed_refunds',
        verbose_name='审核员'
    )
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name='审核时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '退款申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.donation.order_no} - {self.get_status_display()}'

    @transaction.atomic
    def approve(self, reviewer, refund_transaction_id=None):
        from django.utils import timezone

        if self.status != RefundRequestStatus.PENDING:
            raise ValueError('该申请已处理，无法重复审核')

        self.donation.refund(refund_transaction_id)

        self.status = RefundRequestStatus.APPROVED
        self.reviewer = reviewer
        self.reviewed_at = timezone.now()
        self.save()

        return self

    @transaction.atomic
    def reject(self, reviewer, review_reason):
        from django.utils import timezone

        if self.status != RefundRequestStatus.PENDING:
            raise ValueError('该申请已处理，无法重复审核')

        if not review_reason:
            raise ValueError('拒绝时必须填写审核意见')

        self.status = RefundRequestStatus.REJECTED
        self.reviewer = reviewer
        self.review_reason = review_reason
        self.reviewed_at = timezone.now()
        self.save()

        return self

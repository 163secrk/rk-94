import hashlib
import hmac
from django.conf import settings
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
            DonationCertificate.check_and_issue_for_donation(self)
            UserHonorProfile.get_or_create_for_user(self.user).recalculate()
        elif new_status == DonationStatus.REFUNDED:
            self.refunded_at = timezone.now()
            if old_status == DonationStatus.PAID:
                self._update_project_amount(-self.amount)
                UserHonorProfile.get_or_create_for_user(self.user).recalculate()

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
            DonationCertificate.check_and_issue_for_project_success(project)

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

        UserHonorProfile.get_or_create_for_user(self.user).recalculate()

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


class UpdateType(models.TextChoices):
    TEXT = 'text', _('文字动态')
    IMAGE = 'image', _('图片动态')
    VIDEO = 'video', _('视频动态')
    MIXED = 'mixed', _('混合动态')


class NotificationType(models.TextChoices):
    PROJECT_UPDATE = 'project_update', _('项目进展')
    DONATION_SUCCESS = 'donation_success', _('捐赠成功')
    PROJECT_COMPLETED = 'project_completed', _('项目完成')
    SYSTEM = 'system', _('系统通知')


class ProjectUpdate(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='updates',
        verbose_name='所属项目'
    )
    initiator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_updates',
        verbose_name='发布人'
    )
    title = models.CharField(max_length=200, verbose_name='动态标题')
    content = models.TextField(verbose_name='动态内容')
    update_type = models.CharField(
        max_length=20,
        choices=UpdateType.choices,
        default=UpdateType.TEXT,
        verbose_name='动态类型'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '项目进展'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.project.title} - {self.title}'

    def save(self, *args, **kwargs):
        has_images = self.images.exists() if self.pk else False
        has_videos = self.videos.exists() if self.pk else False
        if has_images and has_videos:
            self.update_type = UpdateType.MIXED
        elif has_images:
            self.update_type = UpdateType.IMAGE
        elif has_videos:
            self.update_type = UpdateType.VIDEO
        else:
            self.update_type = UpdateType.TEXT
        super().save(*args, **kwargs)

    def notify_donors(self):
        from django.utils import timezone
        donor_ids = Donation.objects.filter(
            project=self.project,
            status=DonationStatus.PAID
        ).values_list('user_id', flat=True).distinct()

        notifications = []
        for donor_id in donor_ids:
            notifications.append(Notification(
                user_id=donor_id,
                notification_type=NotificationType.PROJECT_UPDATE,
                title=f'【项目进展】{self.project.title}',
                content=self.title,
                related_project_id=self.project_id,
                related_update_id=self.pk,
                created_at=timezone.now()
            ))

        if notifications:
            Notification.objects.bulk_create(notifications)


class ProjectUpdateImage(models.Model):
    project_update = models.ForeignKey(
        ProjectUpdate,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='所属动态'
    )
    image = models.ImageField(upload_to='project_updates/images/', verbose_name='图片')
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name='图片描述')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        verbose_name = '进展图片'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f'{self.project_update.title} - 图片{self.id}'


class ProjectUpdateVideo(models.Model):
    project_update = models.ForeignKey(
        ProjectUpdate,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name='所属动态'
    )
    video = models.FileField(upload_to='project_updates/videos/', verbose_name='视频文件')
    cover_image = models.ImageField(upload_to='project_updates/video_covers/', blank=True, null=True, verbose_name='视频封面')
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name='视频描述')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        verbose_name = '进展视频'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f'{self.project_update.title} - 视频{self.id}'


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='接收用户'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        verbose_name='通知类型'
    )
    title = models.CharField(max_length=200, verbose_name='通知标题')
    content = models.TextField(verbose_name='通知内容')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    read_at = models.DateTimeField(blank=True, null=True, verbose_name='阅读时间')
    related_project_id = models.IntegerField(blank=True, null=True, verbose_name='关联项目ID')
    related_update_id = models.IntegerField(blank=True, null=True, verbose_name='关联动态ID')
    related_donation_id = models.IntegerField(blank=True, null=True, verbose_name='关联捐赠ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.title}'

    def mark_as_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class BadgeLevel(models.TextChoices):
    BRONZE = 'bronze', _('铜心勋章')
    SILVER = 'silver', _('银心勋章')
    GOLD = 'gold', _('金心勋章')
    DIAMOND = 'diamond', _('钻石心勋章')


BADGE_THRESHOLDS = {
    BadgeLevel.BRONZE: 100,
    BadgeLevel.SILVER: 500,
    BadgeLevel.GOLD: 2000,
    BadgeLevel.DIAMOND: 5000,
}

BADGE_RECEIPT_PERMISSIONS = {
    BadgeLevel.BRONZE: 'electronic',
    BadgeLevel.SILVER: 'paper',
    BadgeLevel.GOLD: 'paper_with_letter',
    BadgeLevel.DIAMOND: 'paper_with_gift',
}


class ReceiptType(models.TextChoices):
    ELECTRONIC = 'electronic', _('电子收据')
    PAPER = 'paper', _('纸质收据')
    PAPER_WITH_LETTER = 'paper_with_letter', _('纸质收据（含感谢信）')
    PAPER_WITH_GIFT = 'paper_with_gift', _('纸质收据（含纪念品）')


BADGE_MIN_RECEIPT_TYPE = {
    BadgeLevel.BRONZE: ReceiptType.ELECTRONIC,
    BadgeLevel.SILVER: ReceiptType.PAPER,
    BadgeLevel.GOLD: ReceiptType.PAPER_WITH_LETTER,
    BadgeLevel.DIAMOND: ReceiptType.PAPER_WITH_GIFT,
}


class UserHonorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='honor_profile',
        verbose_name='用户'
    )
    total_donation_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name='累计捐赠金额（元）'
    )
    consecutive_donation_days = models.IntegerField(default=0, verbose_name='连续捐赠天数')
    love_points = models.IntegerField(default=0, verbose_name='爱心值')
    current_badge_level = models.CharField(
        max_length=20,
        choices=BadgeLevel.choices,
        blank=True, null=True,
        verbose_name='当前勋章等级'
    )
    last_donation_date = models.DateField(blank=True, null=True, verbose_name='最后捐赠日期')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户荣誉档案'
        verbose_name_plural = verbose_name

    def __str__(self):
        badge_display = self.get_current_badge_level_display() or '无勋章'
        return f'{self.user.username} - 爱心值{self.love_points} - {badge_display}'

    @property
    def donation_points(self):
        return int(self.total_donation_amount)

    @property
    def streak_points(self):
        return self.consecutive_donation_days * 2

    def recalculate(self):
        from django.db.models import Sum, Min

        paid_donations = Donation.objects.filter(
            user=self.user, status=DonationStatus.PAID
        )

        self.total_donation_amount = paid_donations.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        donation_dates = list(
            paid_donations.values_list('paid_at__date', flat=True)
            .distinct().order_by('-paid_at__date')
        )

        self.consecutive_donation_days = self._calculate_streak(donation_dates)

        if donation_dates:
            self.last_donation_date = donation_dates[0]

        self.love_points = self.donation_points + self.streak_points

        old_badge = self.current_badge_level
        new_badge = self._compute_badge_level()
        self.current_badge_level = new_badge

        self.save()

        if new_badge != old_badge:
            self._sync_badges()

    def _calculate_streak(self, donation_dates):
        if not donation_dates:
            return 0

        from django.utils import timezone as tz
        today = tz.now().date()

        streak = 0
        expected_date = today

        for d in donation_dates:
            if d == expected_date:
                streak += 1
                expected_date = d - __import__('datetime').timedelta(days=1)
            elif d == expected_date - __import__('datetime').timedelta(days=1):
                streak += 1
                expected_date = d - __import__('datetime').timedelta(days=1)
            else:
                break

        if streak == 0 and donation_dates[0] >= today - __import__('datetime').timedelta(days=1):
            streak = 1

        return streak

    def _compute_badge_level(self):
        level = None
        for badge_level, threshold in BADGE_THRESHOLDS.items():
            if self.love_points >= threshold:
                level = badge_level
        return level

    def _sync_badges(self):
        if not self.current_badge_level:
            return

        earned_levels = set(
            UserBadge.objects.filter(user=self.user, is_lit=True)
            .values_list('badge_level', flat=True)
        )

        for badge_level, threshold in BADGE_THRESHOLDS.items():
            if self.love_points >= threshold:
                if badge_level not in earned_levels:
                    UserBadge.objects.create(
                        user=self.user,
                        badge_level=badge_level,
                        is_lit=True
                    )

    def can_request_receipt_type(self, receipt_type):
        if not self.current_badge_level:
            return False

        level_order = list(BADGE_THRESHOLDS.keys())
        user_idx = level_order.index(self.current_badge_level) if self.current_badge_level in level_order else -1

        type_order = [ReceiptType.ELECTRONIC, ReceiptType.PAPER, ReceiptType.PAPER_WITH_LETTER, ReceiptType.PAPER_WITH_GIFT]
        type_idx = type_order.index(receipt_type) if receipt_type in type_order else len(type_order)

        min_badge_for_type = None
        for bl, rt in BADGE_MIN_RECEIPT_TYPE.items():
            if rt == receipt_type:
                min_badge_for_type = bl
                break

        if min_badge_for_type is None:
            return False

        min_idx = level_order.index(min_badge_for_type)
        return user_idx >= min_idx

    @classmethod
    def get_or_create_for_user(cls, user):
        profile, created = cls.objects.get_or_create(user=user)
        if created or profile.love_points == 0:
            profile.recalculate()
        return profile


class UserBadge(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name='用户'
    )
    badge_level = models.CharField(
        max_length=20,
        choices=BadgeLevel.choices,
        verbose_name='勋章等级'
    )
    is_lit = models.BooleanField(default=True, verbose_name='是否点亮')
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name='获得时间')

    class Meta:
        verbose_name = '用户勋章'
        verbose_name_plural = verbose_name
        unique_together = [['user', 'badge_level']]
        ordering = ['earned_at']

    def __str__(self):
        status = '已点亮' if self.is_lit else '未点亮'
        return f'{self.user.username} - {self.get_badge_level_display()} ({status})'


class ReceiptRequestStatus(models.TextChoices):
    PENDING = 'pending', _('待审核')
    APPROVED = 'approved', _('已通过')
    REJECTED = 'rejected', _('已拒绝')
    MAILED = 'mailed', _('已邮寄')


class ReceiptRequest(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='receipt_requests',
        verbose_name='申请人'
    )
    donations = models.ManyToManyField(
        Donation,
        related_name='receipt_requests',
        verbose_name='关联捐赠'
    )
    receipt_type = models.CharField(
        max_length=30,
        choices=ReceiptType.choices,
        verbose_name='收据类型'
    )
    badge_level_at_request = models.CharField(
        max_length=20,
        choices=BadgeLevel.choices,
        verbose_name='申请时勋章等级'
    )
    love_points_at_request = models.IntegerField(verbose_name='申请时爱心值')
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='收据金额合计（元）'
    )
    recipient_name = models.CharField(max_length=100, verbose_name='收件人姓名')
    recipient_address = models.CharField(max_length=500, verbose_name='收件地址')
    recipient_phone = models.CharField(max_length=20, verbose_name='联系电话')
    status = models.CharField(
        max_length=20,
        choices=ReceiptRequestStatus.choices,
        default=ReceiptRequestStatus.PENDING,
        verbose_name='申请状态'
    )
    reject_reason = models.TextField(blank=True, null=True, verbose_name='拒绝原因')
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='reviewed_receipt_requests',
        verbose_name='审核人'
    )
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name='审核时间')
    tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='快递单号')
    mailed_at = models.DateTimeField(blank=True, null=True, verbose_name='邮寄时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '捐赠收据申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.get_receipt_type_display()} - {self.get_status_display()}'


class CertificateType(models.TextChoices):
    DONATION_THRESHOLD = 'donation_threshold', _('大额捐赠证书')
    PROJECT_SUCCESS = 'project_success', _('项目筹款成功证书')


class DonationCertificate(models.Model):
    certificate_no = models.CharField(max_length=64, unique=True, verbose_name='证书编号')
    certificate_type = models.CharField(
        max_length=30,
        choices=CertificateType.choices,
        verbose_name='证书类型'
    )
    donation = models.ForeignKey(
        Donation,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='关联捐赠'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='donation_certificates',
        verbose_name='捐赠人'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='所属项目'
    )
    donation_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='捐赠金额（元）')
    integrity_hash = models.CharField(max_length=128, verbose_name='完整性校验哈希')
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name='颁发时间')

    class Meta:
        verbose_name = '捐赠证书'
        verbose_name_plural = verbose_name
        ordering = ['-issued_at']

    def __str__(self):
        return f'{self.certificate_no} - {self.user.username}'

    @classmethod
    def _get_certificate_secret(cls):
        return getattr(settings, 'CERTIFICATE_HMAC_SECRET', settings.SECRET_KEY)

    @classmethod
    def generate_certificate_no(cls, project_id, date_str=None):
        from django.utils import timezone as tz

        if date_str is None:
            date_str = tz.now().strftime('%Y%m%d')

        prefix = f'PRJ{project_id:04d}'
        date_part = date_str

        with transaction.atomic():
            existing_count = cls.objects.filter(
                certificate_no__startswith=f'{prefix}-{date_part}-'
            ).select_for_update().count()

            seq = existing_count + 1
            certificate_no = f'{prefix}-{date_part}-{seq:04d}'

            while cls.objects.filter(certificate_no=certificate_no).exists():
                seq += 1
                certificate_no = f'{prefix}-{date_part}-{seq:04d}'

        return certificate_no

    @classmethod
    def compute_integrity_hash(cls, certificate_no, donation_id, user_id, project_id, donation_amount, issued_at_str):
        secret = cls._get_certificate_secret().encode('utf-8')
        message = f'{certificate_no}|{donation_id}|{user_id}|{project_id}|{donation_amount}|{issued_at_str}'
        return hmac.new(secret, message.encode('utf-8'), hashlib.sha256).hexdigest()

    def verify_integrity(self):
        issued_at_str = self.issued_at.strftime('%Y-%m-%d %H:%M:%S.%f')
        expected_hash = self.compute_integrity_hash(
            self.certificate_no,
            self.donation_id,
            self.user_id,
            self.project_id,
            str(self.donation_amount),
            issued_at_str
        )
        return hmac.compare_digest(self.integrity_hash, expected_hash)

    @classmethod
    @transaction.atomic
    def issue_certificate(cls, donation, certificate_type):
        from django.utils import timezone as tz

        if cls.objects.filter(donation=donation, certificate_type=certificate_type).exists():
            return None

        certificate_no = cls.generate_certificate_no(donation.project_id)

        cert = cls(
            certificate_no=certificate_no,
            certificate_type=certificate_type,
            donation=donation,
            user=donation.user,
            project=donation.project,
            donation_amount=donation.amount,
        )
        cert.save()

        issued_at_str = cert.issued_at.strftime('%Y-%m-%d %H:%M:%S.%f')
        cert.integrity_hash = cls.compute_integrity_hash(
            cert.certificate_no,
            cert.donation_id,
            cert.user_id,
            cert.project_id,
            str(cert.donation_amount),
            issued_at_str
        )
        cert.save(update_fields=['integrity_hash'])

        return cert

    @classmethod
    def check_and_issue_for_donation(cls, donation):
        threshold = Decimal(getattr(settings, 'CERTIFICATE_DONATION_THRESHOLD', '1000'))

        if donation.amount >= threshold:
            cls.issue_certificate(donation, CertificateType.DONATION_THRESHOLD)

    @classmethod
    def check_and_issue_for_project_success(cls, project):
        paid_donations = Donation.objects.filter(
            project=project,
            status=DonationStatus.PAID
        )

        for donation in paid_donations:
            cls.issue_certificate(donation, CertificateType.PROJECT_SUCCESS)

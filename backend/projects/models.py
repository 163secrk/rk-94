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
    COMPLETED = 'completed', _('已完成')


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
    transaction_id = models.CharField(max_length=64, blank=True, null=True, verbose_name='交易流水号')
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
    def refund(self):
        return self.update_status(DonationStatus.REFUNDED)

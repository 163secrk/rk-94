from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

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

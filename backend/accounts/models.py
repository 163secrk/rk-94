from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    DONOR = 'donor', _('捐赠人')
    INITIATOR = 'initiator', _('项目发起方')
    AUDITOR = 'auditor', _('平台审核员')


class VerificationStatus(models.TextChoices):
    PENDING = 'pending', _('待审核')
    APPROVED = 'approved', _('已通过')
    REJECTED = 'rejected', _('已拒绝')


class ProfileType(models.TextChoices):
    PERSONAL = 'personal', _('个人')
    ENTERPRISE = 'enterprise', _('企业')


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DONOR,
        verbose_name='用户角色'
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.username} - {self.get_role_display()}'

    @property
    def is_verified(self):
        if hasattr(self, 'verification_profile'):
            return self.verification_profile.status == VerificationStatus.APPROVED
        return False


class VerificationProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='verification_profile',
        verbose_name='用户'
    )
    profile_type = models.CharField(
        max_length=20,
        choices=ProfileType.choices,
        verbose_name='档案类型'
    )
    status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        verbose_name='审核状态'
    )
    real_name = models.CharField(max_length=100, verbose_name='真实姓名/企业名称')
    id_card = models.CharField(max_length=50, blank=True, null=True, verbose_name='身份证号/统一社会信用代码')
    
    personal_id_front = models.ImageField(upload_to='verification/', blank=True, null=True, verbose_name='身份证正面')
    personal_id_back = models.ImageField(upload_to='verification/', blank=True, null=True, verbose_name='身份证反面')
    
    enterprise_license = models.ImageField(upload_to='verification/', blank=True, null=True, verbose_name='企业营业执照')
    enterprise_legal_person = models.CharField(max_length=100, blank=True, null=True, verbose_name='企业法人')
    
    reject_reason = models.TextField(blank=True, null=True, verbose_name='拒绝原因')
    verified_at = models.DateTimeField(blank=True, null=True, verbose_name='审核通过时间')
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='提交时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '实名认证档案'
        verbose_name_plural = verbose_name
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.user.username} - {self.get_profile_type_display()} - {self.get_status_display()}'

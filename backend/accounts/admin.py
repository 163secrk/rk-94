from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, VerificationProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_verified', 'is_staff', 'created_at']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'phone']
    fieldsets = UserAdmin.fieldsets + (
        ('扩展信息', {
            'fields': ('role', 'phone', 'avatar')
        }),
    )

    def is_verified(self, obj):
        return obj.is_verified
    is_verified.boolean = True
    is_verified.short_description = '是否实名认证'


@admin.register(VerificationProfile)
class VerificationProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'profile_type', 'real_name', 'status', 'submitted_at', 'verified_at']
    list_filter = ['profile_type', 'status']
    search_fields = ['user__username', 'real_name', 'id_card']
    readonly_fields = ['submitted_at', 'updated_at']
    fieldsets = (
        ('基础信息', {
            'fields': ('user', 'profile_type', 'status', 'real_name', 'id_card')
        }),
        ('个人认证材料', {
            'fields': ('personal_id_front', 'personal_id_back'),
            'classes': ('collapse',)
        }),
        ('企业认证材料', {
            'fields': ('enterprise_license', 'enterprise_legal_person'),
            'classes': ('collapse',)
        }),
        ('审核信息', {
            'fields': ('reject_reason', 'verified_at', 'submitted_at', 'updated_at')
        }),
    )

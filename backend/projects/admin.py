from django.contrib import admin
from .models import Project, ProjectBudget, Donation


class ProjectBudgetInline(admin.TabularInline):
    model = ProjectBudget
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'initiator', 'category', 'target_amount', 'current_amount', 'status', 'deadline', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['title', 'description', 'initiator__username']
    inlines = [ProjectBudgetInline]
    readonly_fields = ['created_at', 'updated_at', 'audited_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('initiator', 'title', 'category', 'description', 'detail_content', 'cover_image')
        }),
        ('筹款信息', {
            'fields': ('target_amount', 'current_amount', 'deadline')
        }),
        ('审核信息', {
            'fields': ('status', 'reject_reason', 'auditor', 'audited_at')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectBudget)
class ProjectBudgetAdmin(admin.ModelAdmin):
    list_display = ['project', 'category', 'amount', 'quantity', 'unit', 'subtotal']
    list_filter = ['project__category']
    search_fields = ['project__title', 'category', 'description']


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'user', 'project', 'amount', 'status', 'paid_at', 'created_at']
    list_filter = ['status', 'created_at', 'paid_at']
    search_fields = ['order_no', 'user__username', 'project__title', 'transaction_id']
    readonly_fields = ['order_no', 'created_at', 'updated_at', 'paid_at', 'refunded_at', 'transaction_id']
    fieldsets = (
        ('基本信息', {
            'fields': ('order_no', 'user', 'project', 'amount', 'message')
        }),
        ('状态信息', {
            'fields': ('status', 'paid_at', 'refunded_at', 'transaction_id')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

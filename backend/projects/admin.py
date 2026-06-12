from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
from .models import (
    Project, ProjectBudget, Donation, RefundRequest,
    ProjectStatus, RefundRequestStatus,
    Expenditure, ExpenditureInvoice, DonationExpenditure, ExpenditureType,
    DonationCertificate, CertificateType,
    ProjectUpdate, ProjectUpdateImage, ProjectUpdateVideo, UpdateType,
    Notification, NotificationType
)


class ProjectBudgetInline(admin.TabularInline):
    model = ProjectBudget
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'initiator', 'category', 'target_amount', 'current_amount', 'used_amount', 'execution_ratio_display', 'status', 'deadline', 'created_at']
    list_filter = ['status', 'category', 'created_at', 'start_date']
    search_fields = ['title', 'description', 'initiator__username']
    inlines = [ProjectBudgetInline]
    readonly_fields = ['created_at', 'updated_at', 'audited_at', 'execution_ratio_display']
    actions = ['start_project_execution']
    fieldsets = (
        ('基本信息', {
            'fields': ('initiator', 'title', 'category', 'description', 'detail_content', 'cover_image')
        }),
        ('筹款信息', {
            'fields': ('target_amount', 'current_amount', 'used_amount', 'execution_ratio_display', 'start_date', 'deadline')
        }),
        ('审核信息', {
            'fields': ('status', 'reject_reason', 'auditor', 'audited_at')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def execution_ratio_display(self, obj):
        return f'{float(obj.execution_ratio * 100):.2f}%'
    execution_ratio_display.short_description = '执行比例'

    @admin.action(description='开始项目执行')
    def start_project_execution(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for project in queryset:
            if project.status == ProjectStatus.FUNDING and project.current_amount > 0:
                project.status = ProjectStatus.EXECUTING
                project.start_date = timezone.now().date()
                project.save()
                updated += 1
        self.message_user(request, ngettext(
            '%d 个项目已进入执行期。',
            '%d 个项目已进入执行期。',
            updated,
        ) % updated, messages.SUCCESS)


@admin.register(ProjectBudget)
class ProjectBudgetAdmin(admin.ModelAdmin):
    list_display = ['project', 'category', 'amount', 'quantity', 'unit', 'subtotal']
    list_filter = ['project__category']
    search_fields = ['project__title', 'category', 'description']


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'user', 'project', 'amount', 'refund_amount', 'platform_fee', 'status', 'paid_at', 'refunded_at', 'created_at']
    list_filter = ['status', 'created_at', 'paid_at', 'refunded_at']
    search_fields = ['order_no', 'user__username', 'project__title', 'transaction_id', 'refund_transaction_id']
    readonly_fields = ['order_no', 'created_at', 'updated_at', 'paid_at', 'refunded_at', 'transaction_id', 'refund_transaction_id', 'execution_ratio_at_refund']
    fieldsets = (
        ('基本信息', {
            'fields': ('order_no', 'user', 'project', 'amount', 'message')
        }),
        ('状态信息', {
            'fields': ('status', 'paid_at', 'refunded_at', 'transaction_id', 'refund_transaction_id')
        }),
        ('退款信息', {
            'fields': ('refund_amount', 'platform_fee', 'execution_ratio_at_refund'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'donation_order_no', 'user', 'donation_amount', 'status', 'created_at', 'reviewed_at']
    list_filter = ['status', 'created_at', 'reviewed_at']
    search_fields = ['donation__order_no', 'user__username', 'reason', 'review_reason']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at']
    actions = ['approve_refund', 'reject_refund']
    fieldsets = (
        ('申请信息', {
            'fields': ('donation', 'user', 'reason')
        }),
        ('审核信息', {
            'fields': ('status', 'review_reason', 'reviewer', 'reviewed_at')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def donation_order_no(self, obj):
        return obj.donation.order_no
    donation_order_no.short_description = '捐赠订单号'
    donation_order_no.admin_order_field = 'donation__order_no'

    def donation_amount(self, obj):
        return obj.donation.amount
    donation_amount.short_description = '捐赠金额'

    @admin.action(description='通过退款申请')
    def approve_refund(self, request, queryset):
        updated = 0
        for refund_request in queryset:
            if refund_request.status == RefundRequestStatus.PENDING:
                try:
                    refund_request.approve(request.user)
                    updated += 1
                except ValueError as e:
                    self.message_user(request, f'申请ID {refund_request.id} 处理失败: {str(e)}', messages.ERROR)
        self.message_user(request, ngettext(
            '%d 个退款申请已通过。',
            '%d 个退款申请已通过。',
            updated,
        ) % updated, messages.SUCCESS)

    @admin.action(description='拒绝退款申请')
    def reject_refund(self, request, queryset):
        updated = 0
        for refund_request in queryset:
            if refund_request.status == RefundRequestStatus.PENDING:
                try:
                    refund_request.reject(request.user, '管理员批量拒绝')
                    updated += 1
                except ValueError as e:
                    self.message_user(request, f'申请ID {refund_request.id} 处理失败: {str(e)}', messages.ERROR)
        self.message_user(request, ngettext(
            '%d 个退款申请已拒绝。',
            '%d 个退款申请已拒绝。',
            updated,
        ) % updated, messages.SUCCESS)


class ExpenditureInvoiceInline(admin.TabularInline):
    model = ExpenditureInvoice
    extra = 1
    readonly_fields = ['created_at']


class DonationExpenditureInline(admin.TabularInline):
    model = DonationExpenditure
    extra = 1
    readonly_fields = ['created_at']
    fk_name = 'expenditure'


@admin.register(Expenditure)
class ExpenditureAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'expenditure_type_display', 'title', 'amount', 'allocated_amount_display', 'invoices_total_display', 'recipient', 'expenditure_date', 'created_at']
    list_filter = ['expenditure_type', 'expenditure_date', 'created_at', 'project__category']
    search_fields = ['title', 'description', 'recipient', 'project__title', 'remark']
    readonly_fields = ['created_at', 'updated_at', 'allocated_amount_display', 'invoices_total_display']
    inlines = [ExpenditureInvoiceInline, DonationExpenditureInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('project', 'expenditure_type', 'title', 'amount', 'expenditure_date')
        }),
        ('详细信息', {
            'fields': ('description', 'recipient', 'operator', 'remark')
        }),
        ('统计信息', {
            'fields': ('allocated_amount_display', 'invoices_total_display'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def expenditure_type_display(self, obj):
        return obj.get_expenditure_type_display()
    expenditure_type_display.short_description = '支出类型'
    expenditure_type_display.admin_order_field = 'expenditure_type'

    def allocated_amount_display(self, obj):
        return f'¥{float(obj.allocated_amount):.2f}'
    allocated_amount_display.short_description = '已分配捐款金额'

    def invoices_total_display(self, obj):
        return f'¥{float(obj.invoices_total):.2f}'
    invoices_total_display.short_description = '发票总金额'

    def save_model(self, request, obj, form, change):
        if not obj.operator:
            obj.operator = request.user
        super().save_model(request, obj, form, change)


@admin.register(ExpenditureInvoice)
class ExpenditureInvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'expenditure', 'invoice_no', 'amount', 'issuer', 'issued_date', 'uploaded_by', 'created_at']
    list_filter = ['issued_date', 'created_at']
    search_fields = ['invoice_no', 'issuer', 'expenditure__title', 'remark']
    readonly_fields = ['created_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('expenditure', 'invoice_file', 'amount')
        }),
        ('发票信息', {
            'fields': ('invoice_no', 'issuer', 'issued_date', 'remark')
        }),
        ('上传信息', {
            'fields': ('uploaded_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DonationExpenditure)
class DonationExpenditureAdmin(admin.ModelAdmin):
    list_display = ['id', 'donation_order_no', 'donor', 'expenditure_title', 'project', 'amount', 'allocated_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['donation__order_no', 'donation__user__username', 'expenditure__title', 'expenditure__project__title']
    readonly_fields = ['created_at']
    fieldsets = (
        ('分配信息', {
            'fields': ('donation', 'expenditure', 'amount')
        }),
        ('操作信息', {
            'fields': ('allocated_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def donation_order_no(self, obj):
        return obj.donation.order_no
    donation_order_no.short_description = '捐赠订单号'
    donation_order_no.admin_order_field = 'donation__order_no'

    def donor(self, obj):
        return obj.donation.user.username
    donor.short_description = '捐赠人'

    def expenditure_title(self, obj):
        return obj.expenditure.title
    expenditure_title.short_description = '支出项目'

    def project(self, obj):
        return obj.expenditure.project.title
    project.short_description = '所属项目'

    def save_model(self, request, obj, form, change):
        if not obj.allocated_by:
            obj.allocated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DonationCertificate)
class DonationCertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_no', 'certificate_type_display', 'user', 'project_title', 'donation_amount', 'integrity_status', 'issued_at']
    list_filter = ['certificate_type', 'issued_at']
    search_fields = ['certificate_no', 'user__username', 'project__title']
    readonly_fields = ['certificate_no', 'certificate_type', 'donation', 'user', 'project', 'donation_amount', 'integrity_hash', 'integrity_status', 'issued_at']
    fieldsets = (
        ('证书信息', {
            'fields': ('certificate_no', 'certificate_type', 'donation_amount', 'issued_at')
        }),
        ('关联信息', {
            'fields': ('donation', 'user', 'project')
        }),
        ('安全信息', {
            'fields': ('integrity_hash', 'integrity_status'),
            'classes': ('collapse',)
        }),
    )

    def certificate_type_display(self, obj):
        return obj.get_certificate_type_display()
    certificate_type_display.short_description = '证书类型'
    certificate_type_display.admin_order_field = 'certificate_type'

    def project_title(self, obj):
        return obj.project.title
    project_title.short_description = '所属项目'
    project_title.admin_order_field = 'project__title'

    def integrity_status(self, obj):
        return '✓ 有效' if obj.verify_integrity() else '✗ 已被篡改'
    integrity_status.short_description = '完整性校验'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ProjectUpdateImageInline(admin.TabularInline):
    model = ProjectUpdateImage
    extra = 1
    readonly_fields = ['created_at']


class ProjectUpdateVideoInline(admin.TabularInline):
    model = ProjectUpdateVideo
    extra = 1
    readonly_fields = ['created_at']


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ['id', 'project_title', 'title', 'initiator', 'update_type_display', 'images_count', 'videos_count', 'created_at']
    list_filter = ['update_type', 'created_at', 'project__category']
    search_fields = ['title', 'content', 'project__title', 'initiator__username']
    readonly_fields = ['created_at', 'updated_at', 'update_type']
    inlines = [ProjectUpdateImageInline, ProjectUpdateVideoInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('project', 'initiator', 'title', 'content', 'update_type')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def project_title(self, obj):
        return obj.project.title
    project_title.short_description = '所属项目'
    project_title.admin_order_field = 'project__title'

    def update_type_display(self, obj):
        return obj.get_update_type_display()
    update_type_display.short_description = '动态类型'
    update_type_display.admin_order_field = 'update_type'

    def images_count(self, obj):
        return obj.images.count()
    images_count.short_description = '图片数'

    def videos_count(self, obj):
        return obj.videos.count()
    videos_count.short_description = '视频数'


@admin.register(ProjectUpdateImage)
class ProjectUpdateImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'project_update_title', 'image_preview', 'description', 'sort_order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['project_update__title', 'description']
    readonly_fields = ['created_at']

    def project_update_title(self, obj):
        return obj.project_update.title
    project_update_title.short_description = '所属动态'
    project_update_title.admin_order_field = 'project_update__title'

    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html(f'<img src="{obj.image.url}" width="60" height="60" style="object-fit:cover;border-radius:4px;" />')
        return '-'
    image_preview.short_description = '预览'


@admin.register(ProjectUpdateVideo)
class ProjectUpdateVideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'project_update_title', 'video', 'description', 'sort_order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['project_update__title', 'description']
    readonly_fields = ['created_at']

    def project_update_title(self, obj):
        return obj.project_update.title
    project_update_title.short_description = '所属动态'
    project_update_title.admin_order_field = 'project_update__title'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'notification_type_display', 'title', 'is_read', 'read_at', 'related_project_id', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['created_at']
    actions = ['mark_as_read', 'mark_as_unread']
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'notification_type', 'title', 'content')
        }),
        ('状态信息', {
            'fields': ('is_read', 'read_at')
        }),
        ('关联信息', {
            'fields': ('related_project_id', 'related_update_id', 'related_donation_id'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def notification_type_display(self, obj):
        return obj.get_notification_type_display()
    notification_type_display.short_description = '通知类型'
    notification_type_display.admin_order_field = 'notification_type'

    @admin.action(description='标记为已读')
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        self.message_user(request, ngettext(
            '%d 条通知已标记为已读。',
            '%d 条通知已标记为已读。',
            updated,
        ) % updated, messages.SUCCESS)

    @admin.action(description='标记为未读')
    def mark_as_unread(self, request, queryset):
        updated = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, ngettext(
            '%d 条通知已标记为未读。',
            '%d 条通知已标记为未读。',
            updated,
        ) % updated, messages.SUCCESS)

from django.contrib import admin
from django.db.models import Sum, Count, Avg
from django.utils.html import format_html
from django.urls import reverse
from .models import Member, NextOfKin, MemberDocument, MemberSavings, MemberActivity, CreditScoreHistory

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        'member_number', 'get_full_name', 'group', 'phone_number',
        'membership_status', 'credit_score', 'risk_category',
        'total_savings', 'get_loan_eligibility'
    ]
    list_filter = [
        'membership_status', 'gender', 'marital_status', 'education_level',
        'risk_category', 'group', 'date_joined', 'id_verified'
    ]
    search_fields = [
        'member_number', 'first_name', 'last_name', 'id_number',
        'phone_number', 'email'
    ]
    readonly_fields = [
        'member_number', 'credit_score', 'risk_category', 'member_since_months',
        'total_savings', 'total_loans_taken', 'total_loans_repaid',
        'total_interest_paid', 'total_welfare_contributions', 'total_fines_charges',
        'savings_consistency', 'loan_repayment_rate', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'member_number', 'user', 'group', 'first_name', 'last_name',
                'id_number', 'phone_number', 'email', 'date_of_birth'
            )
        }),
        ('Personal Details', {
            'fields': (
                'gender', 'marital_status', 'education_level', 'occupation',
                'employer', 'monthly_income'
            )
        }),
        ('Contact Information', {
            'fields': ('address', 'city', 'county', 'postal_code')
        }),
        ('Membership Details', {
            'fields': (
                'date_joined', 'membership_status', 'membership_type',
                'member_since_months'
            )
        }),
        ('Verification', {
            'fields': (
                'id_document', 'id_verified', 'id_verification_date',
                'live_photo', 'biometric_verified'
            )
        }),
        ('Financial Summary', {
            'fields': (
                'total_savings', 'total_loans_taken', 'total_loans_repaid',
                'total_interest_paid', 'total_welfare_contributions',
                'total_fines_charges', 'current_month_savings',
                'current_month_welfare', 'current_month_fines'
            ),
            'classes': ('collapse',)
        }),
        ('Credit Assessment', {
            'fields': (
                'credit_score', 'risk_category', 'savings_consistency',
                'loan_repayment_rate'
            )
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'group')

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

    def get_loan_eligibility(self, obj):
        can_take, reason = obj.can_take_loan()
        if can_take:
            return format_html('<span style="color: green;">✓ Eligible</span>')
        else:
            return format_html('<span style="color: red;" title="{}">✗ Not Eligible</span>', reason)
    get_loan_eligibility.short_description = 'Loan Eligibility'

    def get_urls(self):
        urls = super().get_urls()
        from django.urls import path
        custom_urls = [
            path('<int:member_id>/financial-summary/', self.admin_site.admin_view(self.financial_summary_view), name='member_financial_summary'),
            path('<int:member_id>/credit-history/', self.admin_site.admin_view(self.credit_history_view), name='member_credit_history'),
        ]
        return custom_urls + urls

    def financial_summary_view(self, request, member_id):
        member = Member.objects.get(pk=member_id)
        context = {
            'member': member,
            'financial_summary': member.get_financial_summary(),
            'loan_performance': member.get_loan_performance(),
            'title': f'Financial Summary - {member.get_full_name()}'
        }
        return self.render_template(request, 'admin/members/member/financial_summary.html', context)

    def credit_history_view(self, request, member_id):
        member = Member.objects.get(pk=member_id)
        history = member.credit_score_history.all().order_by('-score_date')
        context = {
            'member': member,
            'credit_history': history,
            'title': f'Credit History - {member.get_full_name()}'
        }
        return self.render_template(request, 'admin/members/member/credit_history.html', context)

@admin.register(NextOfKin)
class NextOfKinAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'member', 'relationship', 'phone_number', 'is_primary_contact', 'verified']
    list_filter = ['relationship', 'is_primary_contact', 'verified']
    search_fields = ['full_name', 'phone_number', 'member__first_name', 'member__last_name']
    readonly_fields = []

    fieldsets = (
        ('Next of Kin Details', {
            'fields': ('member', 'full_name', 'relationship', 'id_number', 'phone_number', 'email', 'address')
        }),
        ('Contact Priority', {
            'fields': ('is_primary_contact', 'contact_priority')
        }),
        ('Verification', {
            'fields': ('id_document', 'verified')
        }),
        ('Additional Information', {
            'fields': ('occupation', 'notes'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MemberDocument)
class MemberDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_name', 'member', 'document_type', 'is_verified', 'upload_date', 'expiry_date']
    list_filter = ['document_type', 'is_verified', 'upload_date', 'expiry_date']
    search_fields = ['document_name', 'member__first_name', 'member__last_name']
    readonly_fields = ['upload_date']

    fieldsets = (
        ('Document Details', {
            'fields': ('member', 'document_type', 'document_name', 'document_file')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verified_date')
        }),
        ('Metadata', {
            'fields': ('expiry_date', 'notes')
        }),
    )

@admin.register(MemberSavings)
class MemberSavingsAdmin(admin.ModelAdmin):
    list_display = ['member', 'transaction_date', 'savings_type', 'amount', 'payment_method', 'is_verified']
    list_filter = ['savings_type', 'payment_method', 'is_verified', 'transaction_date']
    search_fields = ['member__first_name', 'member__last_name', 'receipt_number', 'transaction_reference']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Transaction Details', {
            'fields': ('member', 'transaction_date', 'amount', 'savings_type', 'payment_method')
        }),
        ('References', {
            'fields': ('receipt_number', 'transaction_reference')
        }),
        ('Description', {
            'fields': ('description', 'notes')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member', 'created_by', 'verified_by')

@admin.register(MemberActivity)
class MemberActivityAdmin(admin.ModelAdmin):
    list_display = ['member', 'activity_type', 'activity_date', 'description']
    list_filter = ['activity_type', 'activity_date']
    search_fields = ['member__first_name', 'member__last_name', 'description']
    readonly_fields = ['activity_date']

    fieldsets = (
        ('Activity Details', {
            'fields': ('member', 'activity_type', 'activity_date', 'description')
        }),
        ('Related Objects', {
            'fields': ('related_loan', 'related_savings')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'performed_by'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CreditScoreHistory)
class CreditScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ['member', 'score_date', 'credit_score', 'risk_category', 'score_change']
    list_filter = ['score_date', 'risk_category']
    search_fields = ['member__first_name', 'member__last_name']
    readonly_fields = ['score_change']

    fieldsets = (
        ('Score Details', {
            'fields': ('member', 'score_date', 'credit_score', 'risk_category')
        }),
        ('Factors', {
            'fields': ('savings_consistency', 'loan_repayment_rate', 'membership_duration_months', 'total_fines')
        }),
        ('Change Information', {
            'fields': ('score_change', 'change_reason')
        }),
    )

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Loan, LoanRepayment, IDVerification, LoanTopUp, Guarantor, LoanApplication

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = [
        'loan_number', 'member_name', 'group_name', 'loan_type_display',
        'principal_amount_display', 'total_repayable_display', 'current_balance_display',
        'status_display', 'id_verified_display', 'guarantee_summary_display', 'due_date', 'days_in_arrears_display'
    ]

    list_filter = [
        'loan_type', 'status', 'id_verified', 'application_date',
        'group__county', 'disbursement_date'
    ]

    search_fields = [
        'loan_number', 'member__first_name', 'member__last_name',
        'member__id_number', 'group__name'
    ]

    readonly_fields = [
        'loan_number', 'total_repayable', 'current_balance', 'arrears_amount',
        'days_in_arrears', 'created_at', 'updated_at', 'repayment_schedule_display',
        'loan_performance_display'
    ]

    fieldsets = (
        ('📋 BASIC LOAN INFORMATION', {
            'fields': (
                'loan_number', 'loan_type', 'group', 'member'
            )
        }),

        ('💰 LOAN AMOUNTS & TERMS', {
            'fields': (
                'principal_amount', 'interest_rate', 'total_repayable',
                ('short_term_months', 'long_term_months'),
            )
        }),

        ('📅 DATES & STATUS', {
            'fields': (
                'approval_date',
                ('disbursement_date', 'due_date'),
                'status', 'is_active'
            )
        }),

        ('🆔 ID VERIFICATION', {
            'fields': (
                'id_verified', 'id_verification_method', 'id_verification_date',
                'id_document', 'verified_by'
            )
        }),

        ('📊 REPAYMENT TRACKING', {
            'fields': (
                'total_paid', 'current_balance',
                ('arrears_amount', 'days_in_arrears'),
            )
        }),

        ('🔄 TOP-UP INFORMATION', {
            'fields': (
                'original_loan', 'top_up_amount'
            )
        }),

        ('🏗️ PROJECT LOAN DETAILS', {
            'fields': (
                'project_description', 'project_product'
            )
        }),

        ('📈 LOAN PERFORMANCE', {
            'fields': (
                'repayment_schedule_display', 'loan_performance_display'
            )
        }),

        ('👤 AUDIT INFORMATION', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            )
        }),
    )

    def member_name(self, obj):
        return obj.member.get_full_name()
    member_name.short_description = 'Member'

    def group_name(self, obj):
        return obj.group.name
    group_name.short_description = 'Group'

    def loan_type_display(self, obj):
        type_map = {
            'short_term': '⏱️ Short Term',
            'long_term': '📈 Long Term',
            'project': '🏗️ Project',
            'top_up': '🔄 Top-Up',
        }
        return type_map.get(obj.loan_type, obj.get_loan_type_display())
    loan_type_display.short_description = 'Type'

    def principal_amount_display(self, obj):
        return format_html('<strong>KES {:,}</strong>', obj.principal_amount)
    principal_amount_display.short_description = 'Principal'

    def total_repayable_display(self, obj):
        return format_html('KES {:,}', obj.total_repayable)
    total_repayable_display.short_description = 'Total Repayable'

    def current_balance_display(self, obj):
        color = 'green' if obj.current_balance == 0 else 'orange' if obj.current_balance < obj.principal_amount else 'red'
        return format_html(
            '<span style="color: {};">KES {:,}</span>',
            color, obj.current_balance
        )
    current_balance_display.short_description = 'Balance'

    def status_display(self, obj):
        status_map = {
            'draft': '📝 Draft',
            'applied': '📨 Applied',
            'pending_verification': '🆔 Pending Verification',
            'approved': '✅ Approved',
            'disbursed': '💰 Disbursed',
            'active': '🟢 Active',
            'completed': '🎉 Completed',
            'defaulted': '🔴 Defaulted',
            'rejected': '❌ Rejected',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'

    def id_verified_display(self, obj):
        if obj.id_verified:
            return format_html('✅ Verified')
        return format_html('❌ <strong style="color: red;">NOT VERIFIED</strong>')
    id_verified_display.short_description = 'ID Verified'

    def days_in_arrears_display(self, obj):
        if obj.days_in_arrears > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} days</span>',
                obj.days_in_arrears
            )
        return format_html('<span style="color: green;">Current</span>')
    days_in_arrears_display.short_description = 'Arrears'

    def guarantee_summary_display(self, obj):
        summary = obj.guarantee_summary
        if summary['total_guarantors'] == 0:
            return format_html('<span style="color: orange;">No guarantors</span>')

        color = 'green' if summary['guarantee_coverage_percentage'] >= summary['min_coverage_percentage'] else 'red'
        return format_html(
            '<span style="color: {};">{} guarantors, {}% coverage</span>',
            color,
            summary['approved_guarantors'],
            summary['guarantee_coverage_percentage']
        )
    guarantee_summary_display.short_description = 'Guarantees'

    def repayment_schedule_display(self, obj):
        schedule = obj.get_repayment_schedule()
        if not schedule:
            return "No schedule available"

        html = """
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; max-height: 200px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <thead>
                    <tr style="background: #007bff; color: white;">
                        <th style="padding: 5px; border: 1px solid #ddd;">#</th>
                        <th style="padding: 5px; border: 1px solid #ddd;">Due Date</th>
                        <th style="padding: 5px; border: 1px solid #ddd;">Amount</th>
                        <th style="padding: 5px; border: 1px solid #ddd;">Principal</th>
                        <th style="padding: 5px; border: 1px solid #ddd;">Interest</th>
                    </tr>
                </thead>
                <tbody>
        """

        for installment in schedule[:12]:  # Show first 12 installments
            html += f"""
                <tr>
                    <td style="padding: 5px; border: 1px solid #ddd;">{installment['installment_number']}</td>
                    <td style="padding: 5px; border: 1px solid #ddd;">{installment['due_date']}</td>
                    <td style="padding: 5px; border: 1px solid #ddd;">KES {installment['amount_due']:,.2f}</td>
                    <td style="padding: 5px; border: 1px solid #ddd;">KES {installment['principal']:,.2f}</td>
                    <td style="padding: 5px; border: 1px solid #ddd;">KES {installment['interest']:,.2f}</td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """
        return format_html(html)
    repayment_schedule_display.short_description = 'Repayment Schedule'

    def loan_performance_display(self, obj):
        if obj.total_repayable > 0:
            performance = (obj.total_paid / obj.total_repayable) * 100
            color = 'green' if performance >= 80 else 'orange' if performance >= 50 else 'red'

            html = f"""
            <div style="background: #fff3cd; padding: 10px; border-radius: 5px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>Repayment Performance:</span>
                    <span style="color: {color}; font-weight: bold;">{performance:.1f}%</span>
                </div>
                <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: {color}; height: 100%; width: {performance}%;"></div>
                </div>
                <div style="margin-top: 5px; font-size: 12px;">
                    Paid: KES {obj.total_paid:,.2f} / KES {obj.total_repayable:,.2f}
                </div>
            </div>
            """
            return format_html(html)
        return "No performance data available"
    loan_performance_display.short_description = 'Loan Performance'

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = [
        'loan_link', 'repayment_date', 'amount_paid_display',
        'principal_amount_display', 'interest_amount_display',
        'payment_method_display', 'is_verified_display', 'receipt_number'
    ]

    list_filter = [
        'repayment_date', 'payment_method', 'is_verified', 'loan__loan_type'
    ]

    search_fields = [
        'loan__loan_number', 'receipt_number', 'transaction_reference',
        'loan__member__first_name', 'loan__member__last_name'
    ]

    readonly_fields = ['created_at', 'updated_at']

    def loan_link(self, obj):
        url = reverse('admin:loans_loan_change', args=[obj.loan.id])
        return format_html('<a href="{}">{}</a>', url, obj.loan.loan_number)
    loan_link.short_description = 'Loan'

    def amount_paid_display(self, obj):
        return format_html('<strong>KES {:,}</strong>', obj.amount_paid)
    amount_paid_display.short_description = 'Amount Paid'

    def principal_amount_display(self, obj):
        return format_html('KES {:,}', obj.principal_amount)
    principal_amount_display.short_description = 'Principal'

    def interest_amount_display(self, obj):
        return format_html('KES {:,}', obj.interest_amount)
    interest_amount_display.short_description = 'Interest'

    def payment_method_display(self, obj):
        method_map = {
            'cash': '💵 Cash',
            'mpesa': '📱 M-Pesa',
            'bank': '🏦 Bank',
            'check': '📄 Check',
            'adjustment': '🔄 Adjustment',
        }
        return method_map.get(obj.payment_method, obj.get_payment_method_display())
    payment_method_display.short_description = 'Method'

    def is_verified_display(self, obj):
        if obj.is_verified:
            return format_html('✅ Verified')
        return format_html('🟡 Pending')
    is_verified_display.short_description = 'Verified'

@admin.register(IDVerification)
class IDVerificationAdmin(admin.ModelAdmin):
    list_display = [
        'member_name', 'loan_link', 'verification_method_display',
        'status_display', 'confidence_score_display', 'verified_at', 'expires_at'
    ]

    list_filter = ['status', 'verification_method', 'verified_at', 'id_type']

    search_fields = [
        'member__first_name', 'member__last_name', 'member__id_number',
        'loan__loan_number', 'id_number'
    ]

    readonly_fields = ['created_at', 'updated_at', 'verification_images_display']

    def member_name(self, obj):
        return obj.member.get_full_name()
    member_name.short_description = 'Member'

    def loan_link(self, obj):
        url = reverse('admin:loans_loan_change', args=[obj.loan.id])
        return format_html('<a href="{}">{}</a>', url, obj.loan.loan_number)
    loan_link.short_description = 'Loan'

    def verification_method_display(self, obj):
        method_map = {
            'upload': '📤 Upload',
            'camera': '📷 Live Camera',
            'manual': '👤 Manual',
        }
        return method_map.get(obj.verification_method, obj.get_verification_method_display())
    verification_method_display.short_description = 'Method'

    def status_display(self, obj):
        status_map = {
            'pending': '🟡 Pending',
            'verified': '✅ Verified',
            'rejected': '❌ Rejected',
            'expired': '🕒 Expired',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'

    def confidence_score_display(self, obj):
        if obj.confidence_score >= 80:
            color = 'green'
        elif obj.confidence_score >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, obj.confidence_score
        )
    confidence_score_display.short_description = 'Confidence'

    def verification_images_display(self, obj):
        html = "<div style='display: flex; gap: 10px;'>"
        if obj.id_front_image:
            html += f"""
            <div>
                <strong>Front ID:</strong><br>
                <img src="{obj.id_front_image.url}" style="max-width: 200px; max-height: 150px; border: 1px solid #ddd;">
            </div>
            """
        if obj.id_back_image:
            html += f"""
            <div>
                <strong>Back ID:</strong><br>
                <img src="{obj.id_back_image.url}" style="max-width: 200px; max-height: 150px; border: 1px solid #ddd;">
            </div>
            """
        if obj.live_photo:
            html += f"""
            <div>
                <strong>Live Photo:</strong><br>
                <img src="{obj.live_photo.url}" style="max-width: 200px; max-height: 150px; border: 1px solid #ddd;">
            </div>
            """
        html += "</div>"
        return format_html(html) if obj.id_front_image or obj.id_back_image or obj.live_photo else "No images uploaded"
    verification_images_display.short_description = 'Verification Images'

@admin.register(LoanTopUp)
class LoanTopUpAdmin(admin.ModelAdmin):
    list_display = [
        'original_loan_link', 'top_up_amount_display', 'approval_status_display',
        'previous_repayment_performance_display', 'requires_new_verification_display',
        'created_at'
    ]

    list_filter = ['approval_status', 'requires_new_verification', 'created_at']

    search_fields = [
        'original_loan__loan_number', 'reason',
        'original_loan__member__first_name', 'original_loan__member__last_name'
    ]

    def original_loan_link(self, obj):
        url = reverse('admin:loans_loan_change', args=[obj.original_loan.id])
        return format_html('<a href="{}">{}</a>', url, obj.original_loan.loan_number)
    original_loan_link.short_description = 'Original Loan'

    def top_up_amount_display(self, obj):
        return format_html('<strong>KES {:,}</strong>', obj.top_up_amount)
    top_up_amount_display.short_description = 'Top-up Amount'

    def approval_status_display(self, obj):
        status_map = {
            'pending': '🟡 Pending',
            'approved': '✅ Approved',
            'rejected': '❌ Rejected',
        }
        return status_map.get(obj.approval_status, obj.get_approval_status_display())
    approval_status_display.short_description = 'Status'

    def previous_repayment_performance_display(self, obj):
        color = 'green' if obj.previous_repayment_performance >= 80 else 'orange' if obj.previous_repayment_performance >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, obj.previous_repayment_performance
        )
    previous_repayment_performance_display.short_description = 'Repayment Performance'

    def requires_new_verification_display(self, obj):
        if obj.requires_new_verification:
            return format_html('✅ Required')
        return format_html('❌ Not Required')
    requires_new_verification_display.short_description = 'New Verification'

@admin.register(Guarantor)
class GuarantorAdmin(admin.ModelAdmin):
    list_display = [
        'member_name', 'loan_link', 'guarantee_amount_display',
        'guarantee_percentage_display', 'status_display', 'relationship_display',
        'approved_date', 'created_at'
    ]

    list_filter = ['status', 'relationship', 'approved_date', 'created_at']

    search_fields = [
        'member__first_name', 'member__last_name', 'member__id_number',
        'loan__loan_number'
    ]

    readonly_fields = [
        'created_at', 'updated_at', 'eligibility_check_display',
        'member_savings_display'
    ]

    fieldsets = (
        ('👥 GUARANTOR INFORMATION', {
            'fields': (
                'loan', 'member', 'relationship'
            )
        }),

        ('💰 GUARANTEE DETAILS', {
            'fields': (
                'guarantee_amount', 'guarantee_percentage',
            )
        }),

        ('📋 STATUS & APPROVAL', {
            'fields': (
                'status', 'approved_date', 'approved_by', 'rejection_reason'
            )
        }),

        ('ℹ️ ADDITIONAL INFORMATION', {
            'fields': (
                'notes', 'eligibility_check_display', 'member_savings_display'
            )
        }),

        ('📊 AUDIT INFORMATION', {
            'fields': (
                'created_at', 'updated_at'
            )
        }),
    )

    def member_name(self, obj):
        return obj.member.get_full_name()
    member_name.short_description = 'Member'

    def loan_link(self, obj):
        url = reverse('admin:loans_loan_change', args=[obj.loan.id])
        return format_html('<a href="{}">{}</a>', url, obj.loan.loan_number)
    loan_link.short_description = 'Loan'

    def guarantee_amount_display(self, obj):
        return format_html('<strong>KES {:,}</strong>', obj.guarantee_amount)
    guarantee_amount_display.short_description = 'Guarantee Amount'

    def guarantee_percentage_display(self, obj):
        color = 'green' if obj.guarantee_percentage >= 20 else 'orange'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, obj.guarantee_percentage
        )
    guarantee_percentage_display.short_description = 'Percentage'

    def status_display(self, obj):
        status_map = {
            'pending': '🟡 Pending',
            'approved': '✅ Approved',
            'rejected': '❌ Rejected',
            'withdrawn': '↩️ Withdrawn',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'

    def relationship_display(self, obj):
        relationship_map = {
            'group_member': '👥 Group Member',
            'family': '👨‍👩‍👧‍👦 Family',
            'friend': '👫 Friend',
            'business_partner': '💼 Business Partner',
            'other': '❓ Other',
        }
        return relationship_map.get(obj.relationship, obj.get_relationship_display())
    relationship_display.short_description = 'Relationship'

    def eligibility_check_display(self, obj):
        can_guarantee, reason = obj.can_be_guarantor()
        color = 'green' if can_guarantee else 'red'
        icon = '✅' if can_guarantee else '❌'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, reason
        )
    eligibility_check_display.short_description = 'Eligibility Check'

    def member_savings_display(self, obj):
        try:
            savings = obj.member.get_total_savings()
            return format_html('KES {:,}', savings)
        except:
            return "N/A"
    member_savings_display.short_description = 'Member Total Savings'

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'loan_link', 'applicant_name', 'group_name',
        'principal_amount_display', 'status_display',
        'guarantee_summary_display', 'application_date'
    ]

    list_filter = ['status', 'application_date', 'group']

    search_fields = [
        'loan__loan_number', 'applicant__first_name', 'applicant__last_name',
        'applicant__id_number', 'group__name'
    ]

    readonly_fields = [
        'application_date', 'submitted_date', 'guarantee_coverage_display',
        'guarantor_list_display', 'eligibility_check_display'
    ]

    fieldsets = (
        ('📋 APPLICATION INFORMATION', {
            'fields': (
                'loan', 'applicant', 'group', 'status'
            )
        }),



        ('🛡️ GUARANTOR REQUIREMENTS', {
            'fields': (
                'required_guarantors', 'min_guarantee_percentage',
                'guarantee_coverage_display', 'guarantor_list_display'
            )
        }),

        ('📄 BUSINESS/PROJECT DETAILS', {
            'fields': (
                'project_description', 'business_plan', 'expected_returns'
            )
        }),

        ('👨‍💼 REVIEW INFORMATION', {
            'fields': (
                'reviewed_by', 'reviewed_date', 'review_notes',
                'rejected_by', 'rejection_reason'
            )
        }),

        ('✅ ELIGIBILITY CHECK', {
            'fields': (
                'eligibility_check_display',
            )
        }),

        ('📅 DATES', {
            'fields': (
                'application_date', 'submitted_date'
            )
        }),
    )

    def loan_link(self, obj):
        url = reverse('admin:loans_loan_change', args=[obj.loan.id])
        return format_html('<a href="{}">{}</a>', url, obj.loan.loan_number)
    loan_link.short_description = 'Loan'

    def applicant_name(self, obj):
        return obj.applicant.get_full_name()
    applicant_name.short_description = 'Applicant'

    def group_name(self, obj):
        return obj.group.name
    group_name.short_description = 'Group'

    def principal_amount_display(self, obj):
        return format_html('<strong>KES {:,}</strong>', obj.loan.principal_amount)
    principal_amount_display.short_description = 'Principal Amount'

    def status_display(self, obj):
        status_map = {
            'draft': '📝 Draft',
            'submitted': '📨 Submitted',
            'under_review': '🔍 Under Review',
            'pending_guarantors': '🛡️ Pending Guarantors',
            'pending_verification': '🆔 Pending Verification',
            'approved': '✅ Approved',
            'rejected': '❌ Rejected',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'

    def guarantee_summary_display(self, obj):
        summary = obj.loan.guarantee_summary
        color = 'green' if summary['guarantee_coverage_percentage'] >= obj.min_guarantee_percentage else 'red'

        return format_html(
            '<span style="color: {};">{}/{} guarantors, {}% coverage</span>',
            color,
            summary['approved_guarantors'],
            obj.required_guarantors,
            summary['guarantee_coverage_percentage']
        )
    guarantee_summary_display.short_description = 'Guarantee Summary'

    def guarantee_coverage_display(self, obj):
        coverage = obj.guarantee_coverage_percentage
        color = 'green' if coverage >= obj.min_guarantee_percentage else 'red'

        html = f"""
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Current Coverage:</span>
                <span style="color: {color}; font-weight: bold;">{coverage:.1f}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Required Coverage:</span>
                <span>{obj.min_guarantee_percentage}%</span>
            </div>
            <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                <div style="background: {color}; height: 100%; width: {min(coverage, 100)}%;"></div>
            </div>
            <div style="margin-top: 5px; font-size: 12px;">
                Total Guarantee: KES {obj.total_guarantee_amount:,.2f} / KES {obj.loan.principal_amount:,.2f}
            </div>
        </div>
        """
        return format_html(html)
    guarantee_coverage_display.short_description = 'Guarantee Coverage'

    def guarantor_list_display(self, obj):
        guarantors = obj.loan.guarantors.all()

        if not guarantors:
            return "No guarantors added"

        html = """
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; max-height: 300px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <thead>
                    <tr style="background: #007bff; color: white;">
                        <th style="padding: 5px; border: 1px solid #ddd;">Member</th>
                        <th style="padding: 5px; border: 1px solid #ddd;">Amount</th>
                        <th style="padding: 5px; border: 1px solid #ddd;">Status</th>
                        <th style="padding: 5px; border: 1px solid #ddd;">Relationship</th>
                    </tr>
                </thead>
                <tbody>
        """

        for guarantor in guarantors:
            status_color = {
                'pending': 'orange',
                'approved': 'green',
                'rejected': 'red',
                'withdrawn': 'gray'
            }.get(guarantor.status, 'black')

            html += f"""
                <tr>
                    <td style="padding: 5px; border: 1px solid #ddd;">{guarantor.member.get_full_name()}</td>
                    <td style="padding: 5px; border: 1px solid #ddd;">KES {guarantor.guarantee_amount:,.2f}</td>
                    <td style="padding: 5px; border: 1px solid #ddd; color: {status_color};">{guarantor.get_status_display()}</td>
                    <td style="padding: 5px; border: 1px solid #ddd;">{guarantor.get_relationship_display()}</td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """
        return format_html(html)
    guarantor_list_display.short_description = 'Guarantors List'

    def eligibility_check_display(self, obj):
        can_submit, errors = obj.can_submit()

        if can_submit:
            return format_html('<span style="color: green;">✅ Eligible for submission</span>')
        else:
            error_html = '<span style="color: red;">❌ Cannot submit:</span><ul style="margin: 5px 0; padding-left: 20px;">'
            for error in errors:
                error_html += f'<li>{error}</li>'
            error_html += '</ul>'
            return format_html(error_html)
    eligibility_check_display.short_description = 'Eligibility Check'

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from .models import CashInTransaction, CashOutTransaction, TransactionReconciliation, TransactionCategory

@admin.register(CashInTransaction)
class CashInTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'transaction_date', 'transaction_type_display',
        'amount_display', 'member_link', 'payment_method_display',
        'status_display', 'is_verified_display', 'recorded_by_name'
    ]

    list_filter = [
        'transaction_type', 'status', 'payment_method', 'transaction_date',
        'group', 'is_verified'
    ]

    search_fields = [
        'transaction_id', 'member__first_name', 'member__last_name',
        'receipt_number', 'transaction_reference', 'mpesa_code'
    ]

    readonly_fields = [
        'transaction_id', 'created_at', 'updated_at', 'transaction_summary_display'
    ]

    fieldsets = (
        ('📋 TRANSACTION INFORMATION', {
            'fields': (
                'transaction_id', 'group', 'transaction_date', 'transaction_type'
            )
        }),

        ('💰 AMOUNT & PAYMENT', {
            'fields': (
                'amount', 'payment_method', 'receipt_number', 'transaction_reference', 'mpesa_code'
            )
        }),

        ('👤 RELATED PARTIES', {
            'fields': (
                'member', 'loan'
            )
        }),

        ('📝 DESCRIPTION & DOCUMENTS', {
            'fields': (
                'description', 'notes', 'supporting_document'
            )
        }),

        ('✅ VERIFICATION & STATUS', {
            'fields': (
                'status', 'verified_by', 'verified_date', 'rejection_reason'
            )
        }),

        ('📊 TRANSACTION SUMMARY', {
            'fields': (
                'transaction_summary_display',
            )
        }),

        ('👤 AUDIT INFORMATION', {
            'fields': (
                'recorded_by', 'created_at', 'updated_at'
            )
        }),
    )

    def transaction_type_display(self, obj):
        type_map = {
            'savings': '💰 Savings',
            'loan_repayment': '💳 Loan Repayment',
            'welfare': '👥 Welfare',
            'fine': '⚠️ Fine',
            'membership_fee': '🎫 Membership Fee',
            'donation': '🎁 Donation',
            'investment': '📈 Investment',
            'other_income': '📄 Other Income',
        }
        return type_map.get(obj.transaction_type, obj.get_transaction_type_display())
    transaction_type_display.short_description = 'Type'

    def amount_display(self, obj):
        return format_html('<strong>KES {:,}</strong>', obj.amount)
    amount_display.short_description = 'Amount'

    def member_link(self, obj):
        if obj.member:
            url = reverse('admin:members_member_change', args=[obj.member.id])
            return format_html('<a href="{}">{}</a>', url, obj.member.get_full_name())
        return "N/A"
    member_link.short_description = 'Member'

    def payment_method_display(self, obj):
        method_map = {
            'cash': '💵 Cash',
            'mpesa': '📱 M-Pesa',
            'bank_transfer': '🏦 Bank Transfer',
            'cheque': '📄 Cheque',
            'mobile_banking': '📲 Mobile Banking',
            'other': '❓ Other',
        }
        return method_map.get(obj.payment_method, obj.get_payment_method_display())
    payment_method_display.short_description = 'Method'

    def status_display(self, obj):
        status_map = {
            'pending': '🟡 Pending',
            'verified': '✅ Verified',
            'rejected': '❌ Rejected',
            'reversed': '↩️ Reversed',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'

    def is_verified_display(self, obj):
        if obj.is_verified:
            return format_html('✅ Verified')
        return format_html('❌ Not Verified')
    is_verified_display.short_description = 'Verified'

    def recorded_by_name(self, obj):
        return obj.recorded_by.get_full_name() if obj.recorded_by else 'System'
    recorded_by_name.short_description = 'Recorded By'

    def transaction_summary_display(self, obj):
        summary = obj.get_transaction_summary()

        html = f"""
        <div style="background: #d4edda; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb;">
            <h4 style="margin-top: 0; color: #155724;">📊 Transaction Summary</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div><strong>Transaction ID:</strong> {summary['transaction_id']}</div>
                <div><strong>Type:</strong> {summary['type']}</div>
                <div><strong>Amount:</strong> KES {summary['amount']:,.2f}</div>
                <div><strong>Date:</strong> {summary['date']}</div>
                <div><strong>Status:</strong> {summary['status']}</div>
                <div><strong>Payment Method:</strong> {summary['payment_method']}</div>
                <div><strong>Member:</strong> {summary['member']}</div>
                <div><strong>Verified:</strong> {'Yes' if summary['verified'] else 'No'}</div>
            </div>
        </div>
        """
        return format_html(html)
    transaction_summary_display.short_description = 'Transaction Summary'

@admin.register(CashOutTransaction)
class CashOutTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'transaction_date', 'transaction_type_display',
        'amount_display', 'payee_name', 'payment_method_display',
        'status_display', 'approved_by_name', 'paid_by_name'
    ]

    list_filter = [
        'transaction_type', 'status', 'payment_method', 'transaction_date',
        'group'
    ]

    search_fields = [
        'transaction_id', 'payee_name', 'member__first_name', 'member__last_name',
        'cheque_number', 'mpesa_code'
    ]

    readonly_fields = [
        'transaction_id', 'requested_date', 'created_at', 'updated_at',
        'transaction_summary_display', 'approval_workflow_display'
    ]

    fieldsets = (
        ('📋 TRANSACTION INFORMATION', {
            'fields': (
                'transaction_id', 'group', 'transaction_date', 'transaction_type'
            )
        }),

        ('💰 AMOUNT & PAYMENT', {
            'fields': (
                'amount', 'payment_method', 'cheque_number', 'bank_name', 'bank_account', 'mpesa_code'
            )
        }),

        ('👤 PAYEE INFORMATION', {
            'fields': (
                'payee_name', 'payee_phone', 'payee_id_number', 'member', 'loan'
            )
        }),

        ('📝 DESCRIPTION & DOCUMENTS', {
            'fields': (
                'description', 'purpose', 'notes', 'supporting_document', 'receipt_document'
            )
        }),

        ('✅ APPROVAL WORKFLOW', {
            'fields': (
                'status', 'requested_by', 'requested_date',
                'approved_by', 'approved_date', 'approval_notes',
                'paid_by', 'paid_date', 'rejection_reason'
            )
        }),

        ('📊 TRANSACTION SUMMARY', {
            'fields': (
                'transaction_summary_display',
            )
        }),

        ('🔄 APPROVAL WORKFLOW STATUS', {
            'fields': (
                'approval_workflow_display',
            )
        }),

        ('👤 AUDIT INFORMATION', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            )
        }),
    )

    def transaction_type_display(self, obj):
        type_map = {
            'loan_disbursement': '💸 Loan Disbursement',
            'member_withdrawal': '🏧 Member Withdrawal',
            'operational_expense': '🏢 Operational',
            'welfare_payout': '👥 Welfare Payout',
            'supplier_payment': '🏪 Supplier',
            'staff_salary': '👨‍💼 Staff Salary',
            'utility_bill': '💡 Utility Bill',
            'other_expense': '📄 Other Expense',
        }
        return type_map.get(obj.transaction_type, obj.get_transaction_type_display())
    transaction_type_display.short_description = 'Type'

    def amount_display(self, obj):
        return format_html('<strong style="color: red;">KES {:,}</strong>', obj.amount)
    amount_display.short_description = 'Amount'

    def payment_method_display(self, obj):
        method_map = {
            'cash': '💵 Cash',
            'mpesa': '📱 M-Pesa',
            'bank_transfer': '🏦 Bank Transfer',
            'cheque': '📄 Cheque',
            'mobile_banking': '📲 Mobile Banking',
            'other': '❓ Other',
        }
        return method_map.get(obj.payment_method, obj.get_payment_method_display())
    payment_method_display.short_description = 'Method'

    def status_display(self, obj):
        status_map = {
            'draft': '📝 Draft',
            'pending_approval': '🟡 Pending Approval',
            'approved': '✅ Approved',
            'rejected': '❌ Rejected',
            'paid': '💸 Paid',
            'reversed': '↩️ Reversed',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'

    def approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else 'Not Approved'
    approved_by_name.short_description = 'Approved By'

    def paid_by_name(self, obj):
        return obj.paid_by.get_full_name() if obj.paid_by else 'Not Paid'
    paid_by_name.short_description = 'Paid By'

    def transaction_summary_display(self, obj):
        summary = obj.get_transaction_summary()

        html = f"""
        <div style="background: #f8d7da; padding: 15px; border-radius: 5px; border: 1px solid #f5c6cb;">
            <h4 style="margin-top: 0; color: #721c24;">📊 Cash Out Summary</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div><strong>Transaction ID:</strong> {summary['transaction_id']}</div>
                <div><strong>Type:</strong> {summary['type']}</div>
                <div><strong>Amount:</strong> KES {summary['amount']:,.2f}</div>
                <div><strong>Date:</strong> {summary['date']}</div>
                <div><strong>Status:</strong> {summary['status']}</div>
                <div><strong>Payment Method:</strong> {summary['payment_method']}</div>
                <div><strong>Payee:</strong> {summary['payee']}</div>
                <div><strong>Member:</strong> {summary['member']}</div>
            </div>
        </div>
        """
        return format_html(html)
    transaction_summary_display.short_description = 'Transaction Summary'

    def approval_workflow_display(self, obj):
        steps = [
            ('📝 Draft', obj.status == 'draft'),
            ('🟡 Pending Approval', obj.status == 'pending_approval'),
            ('✅ Approved', obj.status == 'approved'),
            ('💸 Paid', obj.status == 'paid')
        ]

        current_step = next((i for i, (step, active) in enumerate(steps) if active), 0)

        html = '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">'
        html += '<h4 style="margin-top: 0;">🔄 Approval Workflow</h4>'
        html += '<div style="display: flex; justify-content: space-between; align-items: center;">'

        for i, (step, active) in enumerate(steps):
            if i <= current_step:
                color = '#28a745' if active else '#6c757d'
                icon = '✅' if i < current_step else '🟡' if active else '⚪'
            else:
                color = '#e9ecef'
                icon = '⚪'

            html += f"""
            <div style="text-align: center; flex: 1;">
                <div style="background: {color}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
                    {icon} {step}
                </div>
            </div>
            """
            if i < len(steps) - 1:
                html += '<div style="flex: 0.2; text-align: center;">➡️</div>'

        html += '</div></div>'

        # Add action buttons based on current status
        if obj.status == 'draft':
            html += '<div style="margin-top: 10px;">'
            html += '<a href="#" class="button" style="background: #007bff; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Submit for Approval</a>'
            html += '</div>'
        elif obj.status == 'pending_approval':
            html += '<div style="margin-top: 10px;">'
            html += '<a href="#" class="button" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Approve</a>'
            html += '<a href="#" class="button" style="background: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Reject</a>'
            html += '</div>'
        elif obj.status == 'approved':
            html += '<div style="margin-top: 10px;">'
            html += '<a href="#" class="button" style="background: #17a2b8; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Mark as Paid</a>'
            html += '</div>'

        return format_html(html)
    approval_workflow_display.short_description = 'Approval Workflow'

@admin.register(TransactionReconciliation)
class TransactionReconciliationAdmin(admin.ModelAdmin):
    list_display = [
        'reconciliation_id', 'group', 'period_start', 'period_end',
        'total_cash_in_display', 'total_cash_out_display', 'variance_display',
        'status_display', 'reconciliation_date'
    ]

    list_filter = ['status', 'reconciliation_date', 'group']

    search_fields = ['reconciliation_id', 'group__name']

    readonly_fields = [
        'reconciliation_id', 'variance', 'expected_balance', 'created_at', 'updated_at',
        'reconciliation_summary_display'
    ]

    fieldsets = (
        ('📋 RECONCILIATION INFORMATION', {
            'fields': (
                'reconciliation_id', 'group', 'reconciliation_date',
                'period_start', 'period_end'
            )
        }),

        ('💰 FINANCIAL SUMMARY', {
            'fields': (
                'opening_balance', 'total_cash_in', 'total_cash_out',
                'expected_balance', 'actual_balance', 'variance'
            )
        }),

        ('📊 RECONCILIATION SUMMARY', {
            'fields': (
                'reconciliation_summary_display',
            )
        }),

        ('✅ STATUS & COMPLETION', {
            'fields': (
                'status', 'completed_by', 'completed_date',
                'variance_explanation', 'notes'
            )
        }),

        ('👤 AUDIT INFORMATION', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            )
        }),
    )

    def total_cash_in_display(self, obj):
        return format_html('<span style="color: green;">KES {:,}</span>', obj.total_cash_in)
    total_cash_in_display.short_description = 'Cash In'

    def total_cash_out_display(self, obj):
        return format_html('<span style="color: red;">KES {:,}</span>', obj.total_cash_out)
    total_cash_out_display.short_description = 'Cash Out'

    def variance_display(self, obj):
        color = 'green' if obj.variance >= 0 else 'red'
        return format_html('<span style="color: {};">KES {:,}</span>', color, obj.variance)
    variance_display.short_description = 'Variance'

    def status_display(self, obj):
        status_map = {
            'pending': '🟡 Pending',
            'in_progress': '🟠 In Progress',
            'completed': '✅ Completed',
            'disputed': '🔴 Disputed',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'

    def reconciliation_summary_display(self, obj):
        html = f"""
        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border: 1px solid #ffeaa7;">
            <h4 style="margin-top: 0; color: #856404;">📊 Reconciliation Summary</h4>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                <div style="background: #d4edda; padding: 10px; border-radius: 3px;">
                    <strong>Opening Balance:</strong><br>
                    <span style="font-size: 16px; font-weight: bold;">KES {obj.opening_balance:,.2f}</span>
                </div>

                <div style="background: #f8d7da; padding: 10px; border-radius: 3px;">
                    <strong>Actual Balance:</strong><br>
                    <span style="font-size: 16px; font-weight: bold;">KES {obj.actual_balance:,.2f}</span>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                <div style="background: #d1ecf1; padding: 10px; border-radius: 3px;">
                    <strong>Total Cash In:</strong><br>
                    <span style="color: green; font-size: 16px; font-weight: bold;">+ KES {obj.total_cash_in:,.2f}</span>
                </div>

                <div style="background: #f8d7da; padding: 10px; border-radius: 3px;">
                    <strong>Total Cash Out:</strong><br>
                    <span style="color: red; font-size: 16px; font-weight: bold;">- KES {obj.total_cash_out:,.2f}</span>
                </div>
            </div>

            <div style="background: {'#d4edda' if obj.variance >= 0 else '#f8d7da'}; padding: 15px; border-radius: 3px; text-align: center;">
                <strong style="font-size: 18px;">Variance: KES {obj.variance:,.2f}</strong><br>
                <span>{'Surplus' if obj.variance >= 0 else 'Deficit'}</span>
            </div>
        </div>
        """
        return format_html(html)
    reconciliation_summary_display.short_description = 'Reconciliation Summary'

@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category_type_display', 'is_active_display',
        'monthly_budget_display', 'current_month_total_display',
        'budget_utilization_display'
    ]

    list_filter = ['category_type', 'is_active', 'has_budget']

    search_fields = ['name', 'description']

    def category_type_display(self, obj):
        type_map = {
            'income': '💰 Income',
            'expense': '💸 Expense',
        }
        return type_map.get(obj.category_type, obj.get_category_type_display())
    category_type_display.short_description = 'Type'

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('✅ Active')
        return format_html('❌ Inactive')
    is_active_display.short_description = 'Active'

    def monthly_budget_display(self, obj):
        if obj.has_budget:
            return format_html('KES {:,}', obj.monthly_budget)
        return format_html('📊 No Budget')
    monthly_budget_display.short_description = 'Monthly Budget'

    def current_month_total_display(self, obj):
        total = obj.get_current_month_total()
        color = 'green' if obj.category_type == 'income' else 'red'
        return format_html('<span style="color: {};">KES {:,}</span>', color, total)
    current_month_total_display.short_description = 'This Month'

    def budget_utilization_display(self, obj):
        if obj.has_budget and obj.monthly_budget > 0:
            utilization = obj.get_budget_utilization()
            color = 'green' if utilization <= 80 else 'orange' if utilization <= 100 else 'red'
            return format_html(
                '<span style="color: {};">{}%</span>',
                color, round(utilization, 1)
            )
        return format_html('📊 N/A')
    budget_utilization_display.short_description = 'Budget Used'

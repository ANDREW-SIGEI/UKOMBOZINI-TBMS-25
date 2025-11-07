from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Group, CashInTransaction, CashOutTransaction, TRFBalance, GroupMeeting, MeetingAttendance

class CashInTransactionInline(admin.TabularInline):
    model = CashInTransaction
    extra = 1
    fields = ['transaction_type', 'amount', 'transaction_date', 'receipt_number']
    readonly_fields = ['created_at']

class CashOutTransactionInline(admin.TabularInline):
    model = CashOutTransaction
    extra = 1
    fields = ['transaction_type', 'amount', 'transaction_date', 'recipient_name']
    readonly_fields = ['created_at']

class GroupMeetingInline(admin.TabularInline):
    model = GroupMeeting
    extra = 1
    fields = ['meeting_date', 'venue', 'total_attendance', 'is_completed']
    readonly_fields = ['created_at']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'county', 'constituency_display', 'ward_display',
        'village', 'chairperson_name', 'contact_phone',
        'total_members', 'current_balance_display',
        'status_display', 'registration_date', 'view_financials_link'
    ]

    list_filter = [
        'county', 'constituency', 'ward', 'status', 'registration_date', 'field_officer'
    ]

    search_fields = [
        'name', 'registration_number', 'chairperson_name',
        'county', 'constituency', 'village', 'contact_phone'
    ]

    readonly_fields = [
        'registration_date', 'total_members', 'current_balance_display',
        'financial_summary_display', 'created_at_display'
    ]

    fieldsets = (
        ('🏢 BASIC GROUP INFORMATION', {
            'fields': (
                'name', 'registration_number', 'description', 'status'
            )
        }),
        ('📍 GEOGRAPHICAL INFORMATION', {
            'fields': (
                ('county', 'constituency'),
                ('ward', 'location', 'village')
            )
        }),
        ('👥 LEADERSHIP INFORMATION', {
            'fields': (
                ('chairperson_name', 'chairperson_phone', 'chairperson_email'),
                ('secretary_name', 'treasurer_name')
            )
        }),
        ('📞 CONTACT INFORMATION', {
            'fields': (
                ('contact_person', 'contact_phone', 'contact_email'),
            )
        }),
        ('📊 GROUP DETAILS', {
            'fields': (
                ('formation_date', 'registration_date'),
                ('total_members', 'initial_capital', 'current_balance_display')
            )
        }),
        ('💼 MANAGEMENT', {
            'fields': (
                ('created_by', 'field_officer'),
            )
        }),
        ('💰 FINANCIAL SUMMARY', {
            'fields': (
                'financial_summary_display',
            )
        }),
    )

    inlines = [CashInTransactionInline, CashOutTransactionInline, GroupMeetingInline]

    # Custom methods for display
    def constituency_display(self, obj):
        return obj.constituency
    constituency_display.short_description = 'Constituency'

    def ward_display(self, obj):
        return obj.ward
    ward_display.short_description = 'Ward'

    def status_display(self, obj):
        color_map = {
            'active': 'green',
            'inactive': 'orange',
            'suspended': 'red',
            'closed': 'gray'
        }
        color = color_map.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def current_balance_display(self, obj):
        balance = obj.current_balance
        color = 'green' if balance >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">KES {:,}</span>',
            color,
            balance
        )
    current_balance_display.short_description = 'Current Balance'

    def financial_summary_display(self, obj):
        summary = obj.get_financial_summary()
        return format_html("""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <h4 style="margin-top: 0;">Financial Overview</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 5px; border-bottom: 1px solid #ddd;"><strong>Total Cash In:</strong></td>
                        <td style="padding: 5px; border-bottom: 1px solid #ddd; text-align: right;">KES {cash_in:,}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px; border-bottom: 1px solid #ddd;"><strong>Total Cash Out:</strong></td>
                        <td style="padding: 5px; border-bottom: 1px solid #ddd; text-align: right;">KES {cash_out:,}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px; border-bottom: 1px solid #ddd;"><strong>Current Balance:</strong></td>
                        <td style="padding: 5px; border-bottom: 1px solid #ddd; text-align: right;">
                            <span style="color: {balance_color}; font-weight: bold;">KES {balance:,}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>Total Savings:</strong></td>
                        <td style="padding: 5px; text-align: right;">KES {savings:,}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>Total Loans:</strong></td>
                        <td style="padding: 5px; text-align: right;">KES {loans:,}</td>
                    </tr>
                </table>
            </div>
        """,
        cash_in=summary['total_cash_in'],
        cash_out=summary['total_cash_out'],
        balance=summary['current_balance'],
        balance_color='green' if summary['current_balance'] >= 0 else 'red',
        savings=summary['total_savings'],
        loans=summary['total_loans']
        )
    financial_summary_display.short_description = 'Financial Summary'

    def created_at_display(self, obj):
        return obj.registration_date.strftime("%Y-%m-%d %H:%M")
    created_at_display.short_description = 'Registered On'

    def view_financials_link(self, obj):
        url = reverse('admin:groups_cashintransaction_changelist') + f'?group__id__exact={obj.id}'
        return format_html('<a href="{}">View Transactions</a>', url)
    view_financials_link.short_description = 'Financials'

    def get_queryset(self, request):
        qs = super().get_queryset(request).prefetch_related('members')

        # Filter groups based on user type
        if request.user.user_type == 'field_officer':
            # Field officers can only see groups assigned to them
            qs = qs.filter(field_officer=request.user)
        # Admin users can see all groups

        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Field officers cannot modify groups
        if request.user.user_type == 'field_officer':
            # Make all fields readonly for field officers
            for field_name in form.base_fields:
                form.base_fields[field_name].disabled = True
        return form

    def has_add_permission(self, request):
        # Field officers cannot add new groups
        if request.user.user_type == 'field_officer':
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        # Field officers cannot modify groups
        if request.user.user_type == 'field_officer':
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Field officers cannot delete groups
        if request.user.user_type == 'field_officer':
            return False
        return super().has_delete_permission(request, obj)

@admin.register(CashInTransaction)
class CashInTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'group', 'transaction_type_display', 'amount_display',
        'transaction_date', 'receipt_number', 'created_by', 'created_at'
    ]
    list_filter = ['transaction_type', 'transaction_date', 'created_at', 'group__county']
    search_fields = ['group__name', 'receipt_number', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'transaction_date'

    fieldsets = (
        ('💵 CASH IN TRANSACTION DETAILS', {
            'fields': (
                'group', 'transaction_type', 'amount', 'description',
                'transaction_date', 'receipt_number'
            )
        }),
        ('📝 AUDIT INFORMATION', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            )
        }),
    )

    def transaction_type_display(self, obj):
        type_map = {
            'banking': '🏦 Banking',
            'short_term_loans': '⏱️ Short Term Loans',
            'long_term_loans': '📈 Long Term Loans',
            'savings': '💰 Savings',
            'welfare': '🤝 Welfare',
            'education_project': '🎓 Education Project',
            'agriculture_project': '🌾 Agriculture Project',
            'ukombozini_loan': '🏢 Ukombozini Loan',
            'application_fee': '📄 Application Fee',
            'appreciation_fee': '🙏 Appreciation Fee',
        }
        return type_map.get(obj.transaction_type, obj.get_transaction_type_display())
    transaction_type_display.short_description = 'Transaction Type'

    def amount_display(self, obj):
        return format_html('<strong>KES {:,}</strong>', obj.amount)
    amount_display.short_description = 'Amount'

@admin.register(CashOutTransaction)
class CashOutTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'group', 'transaction_type_display', 'amount_display', 'transaction_date',
        'voucher_number', 'recipient_name', 'created_by', 'created_at'
    ]
    list_filter = ['transaction_type', 'transaction_date', 'created_at', 'group__county']
    search_fields = ['group__name', 'voucher_number', 'recipient_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'transaction_date'

    fieldsets = (
        ('💸 CASH OUT TRANSACTION DETAILS', {
            'fields': (
                'group', 'transaction_type', 'amount', 'description',
                'transaction_date', 'voucher_number', 'recipient_name'
            )
        }),
        ('📝 AUDIT INFORMATION', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            )
        }),
    )

    def transaction_type_display(self, obj):
        type_map = {
            'service_fee': '⚙️ Service Fee',
            'welfare': '🤝 Welfare Payment',
            'loan_to_ukombozini': '🏢 Loan to Ukombozini',
            'short_term_loans': '⏱️ Short Term Loans',
            'long_term_loans': '📈 Long Term Loans',
            'operational_costs': '🏢 Operational Costs',
            'dividends': '💰 Dividends Payment',
            'other': '📦 Other Expenses',
        }
        return type_map.get(obj.transaction_type, obj.get_transaction_type_display())
    transaction_type_display.short_description = 'Transaction Type'

    def amount_display(self, obj):
        return format_html('<strong>KES {:,}</strong>', obj.amount)
    amount_display.short_description = 'Amount'

@admin.register(TRFBalance)
class TRFBalanceAdmin(admin.ModelAdmin):
    list_display = [
        'group', 'balance_date', 'balance_account_display', 'short_term_arrears_display',
        'long_term_loans_balance_display', 'net_worth_display', 'created_by'
    ]
    list_filter = ['balance_date', 'created_at', 'group__county']
    search_fields = ['group__name', 'notes']
    readonly_fields = ['net_worth', 'created_at', 'updated_at']
    date_hierarchy = 'balance_date'

    fieldsets = (
        ('📊 BALANCE INFORMATION', {
            'fields': (
                'group', 'balance_date'
            )
        }),
        ('💼 BALANCE ACCOUNTS', {
            'fields': (
                'balance_account', 'short_term_arrears', 'long_term_loans_balance'
            )
        }),
        ('📈 FINANCIAL SUMMARY', {
            'fields': (
                'total_assets', 'total_liabilities', 'net_worth'
            )
        }),
        ('📝 ADDITIONAL INFORMATION', {
            'fields': (
                'notes', 'created_by', 'created_at', 'updated_at'
            )
        }),
    )

    def balance_account_display(self, obj):
        return format_html('KES {:,}', obj.balance_account)
    balance_account_display.short_description = 'Balance A/C'

    def short_term_arrears_display(self, obj):
        color = 'red' if obj.short_term_arrears > 0 else 'green'
        return format_html(
            '<span style="color: {};">KES {:,}</span>',
            color, obj.short_term_arrears
        )
    short_term_arrears_display.short_description = 'Short Term Arrears'

    def long_term_loans_balance_display(self, obj):
        return format_html('KES {:,}', obj.long_term_loans_balance)
    long_term_loans_balance_display.short_description = 'Long Term Loans'

    def net_worth_display(self, obj):
        color = 'green' if obj.net_worth >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">KES {:,}</span>',
            color, obj.net_worth
        )
    net_worth_display.short_description = 'Net Worth'

@admin.register(GroupMeeting)
class GroupMeetingAdmin(admin.ModelAdmin):
    list_display = ['group', 'meeting_date', 'venue', 'total_attendance', 'amount_collected', 'is_completed', 'created_by']
    list_filter = ['meeting_date', 'is_completed', 'created_at']
    search_fields = ['group__name', 'venue', 'agenda']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Meeting Details', {
            'fields': ('group', 'meeting_date', 'venue')
        }),
        ('Meeting Content', {
            'fields': ('agenda', 'minutes')
        }),
        ('Attendance & Finance', {
            'fields': ('total_attendance', 'decisions_made', 'amount_collected', 'is_completed')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MeetingAttendance)
class MeetingAttendanceAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'attended', 'arrival_time', 'contribution_amount']
    list_filter = ['attended', 'meeting__meeting_date']
    search_fields = ['meeting__group__name']

    fieldsets = (
        ('Attendance Details', {
            'fields': ('meeting', 'attended')
        }),
        ('Additional Info', {
            'fields': ('arrival_time', 'contribution_amount', 'comments')
        }),
    )

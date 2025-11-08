from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django import forms
from ukombozini.apps.groups.models import Group
from .models import DividendPeriod, MemberDividend, DividendDistribution, Dividend

class GroupDividendForm(forms.Form):
    """Form for selecting a group to generate dividends"""
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Select Group",
        help_text="Choose a group to generate dividends for all members"
    )

@admin.register(DividendPeriod)
class DividendPeriodAdmin(admin.ModelAdmin):
    list_display = [
        'year', 'start_date', 'end_date', 'net_profit',
        'total_dividend_pool', 'status',
        'visible_to_field_officers', 'visible_to_members',
        'is_current_december', 'group_dividend_actions'
    ]

    def group_dividend_actions(self, obj):
        """Display group-based action buttons in admin list"""
        if obj.status == 'draft' and obj.is_current_december():
            return format_html(
                '<a class="button" href="{}">🎯 Generate Group Dividends</a> ',
                f'{obj.id}/generate-group-dividends/'
            )
        elif obj.status in ['calculated', 'approved']:
            return format_html(
                '<a class="button" href="{}">📊 View All Reports</a> ',
                f'{obj.id}/dividend-reports/'
            )
        return "-"
    group_dividend_actions.short_description = 'Group Actions'

    def get_urls(self):
        """Add custom URLs for group dividend reports"""
        urls = super().get_urls()
        custom_urls = [
            path('<uuid:object_id>/generate-group-dividends/',
                 self.admin_site.admin_view(self.generate_group_dividends_view),
                 name='dividends_dividendperiod_generate-group-dividends'),
            path('<uuid:object_id>/dividend-reports/',
                 self.admin_site.admin_view(self.dividend_reports_view),
                 name='dividends_dividendperiod_dividend-reports'),
            path('<uuid:object_id>/group-report/<int:group_id>/',
                 self.admin_site.admin_view(self.group_dividend_report_view),
                 name='dividends_dividendperiod_group-report'),
        ]
        return custom_urls + urls

    def generate_group_dividends_view(self, request, object_id):
        """View to select a group and generate dividends"""
        period = DividendPeriod.objects.get(id=object_id)

        if request.method == 'POST':
            form = GroupDividendForm(request.POST)
            if form.is_valid():
                group = form.cleaned_data['group']

                # Generate dividends for the selected group
                success, message = period.calculate_dividends_for_group(group)

                if success:
                    self.message_user(request, f"✅ {message}")
                    # Redirect to the group report
                    return self.group_dividend_report_view(request, object_id, group.id)
                else:
                    self.message_user(request, f"❌ {message}", level='ERROR')
        else:
            form = GroupDividendForm()

        context = {
            'title': f'Generate Group Dividends - {period.year}',
            'period': period,
            'form': form,
            'opts': self.model._meta,
            'data_months': period.get_data_collection_months(),
            'month_names': [period.get_month_name(month) for month in period.get_data_collection_months()],
        }

        return render(request, 'admin/dividends/generate_group_dividends.html', context)

    def dividend_reports_view(self, request, object_id):
        """View to see all group dividend reports"""
        period = DividendPeriod.objects.get(id=object_id)

        # Get all groups that have dividends for this period
        groups_with_dividends = Group.objects.filter(
            members__memberdividend__dividend_period=period
        ).distinct()

        group_reports = []
        for group in groups_with_dividends:
            report = period.generate_group_dividends_report(group)
            previous_payments = period.get_previous_payments_for_group(group)
            group_reports.append({
                'group': group,
                'report': report,
                'previous_payments': previous_payments
            })

        context = {
            'title': f'All Group Dividend Reports - {period.year}',
            'period': period,
            'group_reports': group_reports,
            'opts': self.model._meta,
        }

        return render(request, 'admin/dividends/all_group_reports.html', context)

    def group_dividend_report_view(self, request, object_id, group_id):
        """View to display dividend report for a specific group"""
        period = DividendPeriod.objects.get(id=object_id)
        group = Group.objects.get(id=group_id)

        report = period.generate_group_dividends_report(group)
        previous_payments = period.get_previous_payments_for_group(group)

        context = {
            'title': f'Dividend Report - {group.name} ({period.year})',
            'period': period,
            'group': group,
            'report': report,
            'previous_payments': previous_payments,
            'data_months': [period.get_month_name(month) for month in period.DATA_MONTHS],
            'opts': self.model._meta,
        }

        return render(request, 'admin/dividends/group_dividend_report.html', context)

@admin.register(MemberDividend)
class MemberDividendAdmin(admin.ModelAdmin):
    list_display = [
        'member', 'dividend_period', 'savings_based_amount',
        'patronage_based_amount', 'total_dividend', 'distributed',
        'is_visible_to_field_officer', 'is_visible_to_member'
    ]
    list_filter = ['dividend_period', 'distributed', 'calculation_method']
    search_fields = ['member__first_name', 'member__last_name']
    readonly_fields = ['calculated_at', 'is_visible_to_field_officer', 'is_visible_to_member']

    def is_visible_to_field_officer(self, obj):
        return obj.is_visible_to_field_officer()
    is_visible_to_field_officer.boolean = True
    is_visible_to_field_officer.short_description = 'Visible to Officers'

    def is_visible_to_member(self, obj):
        return obj.is_visible_to_member()
    is_visible_to_member.boolean = True
    is_visible_to_member.short_description = 'Visible to Members'

@admin.register(DividendDistribution)
class DividendDistributionAdmin(admin.ModelAdmin):
    list_display = ['dividend_period', 'distribution_date', 'total_distributed']
    list_filter = ['distribution_date', 'dividend_period']
    date_hierarchy = 'distribution_date'

# Legacy admin for backward compatibility
@admin.register(Dividend)
class DividendAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'date', 'description')
    list_filter = ('date', 'user')
    search_fields = ('user__username', 'description')
    ordering = ('-date',)

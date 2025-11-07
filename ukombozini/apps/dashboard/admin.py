from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from .models import MeetingSchedule, FieldVisit, OfficerPerformance, DashboardWidget, OfficerAlert

@admin.register(MeetingSchedule)
class MeetingScheduleAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Filter meetings based on user type
        if request.user.user_type == 'field_officer':
            # Field officers can only see meetings for groups assigned to them
            qs = qs.filter(group__field_officer=request.user)
        # Admin users can see all meetings

        return qs
    list_display = [
        'meeting_id', 'title', 'meeting_type_display', 'scheduled_date',
        'scheduled_time', 'group_link', 'officer_link', 'status_display',
        'attendance_rate_display', 'is_upcoming_display'
    ]

    list_filter = [
        'meeting_type', 'status', 'scheduled_date', 'officer', 'group'
    ]

    search_fields = [
        'meeting_id', 'title', 'group__name', 'officer__username',
        'venue', 'agenda'
    ]

    readonly_fields = [
        'meeting_id', 'created_at', 'updated_at', 'meeting_details_display',
        'attendance_analysis_display'
    ]

    fieldsets = (
        ('📅 MEETING INFORMATION', {
            'fields': (
                'meeting_id', 'title', 'meeting_type', 'group', 'officer'
            )
        }),

        ('🕐 SCHEDULING', {
            'fields': (
                'scheduled_date', 'scheduled_time', 'expected_duration',
                'actual_start_time', 'actual_end_time', 'actual_duration'
            )
        }),

        ('📍 LOCATION', {
            'fields': (
                'venue', 'venue_address', 'gps_coordinates'
            )
        }),

        ('📝 CONTENT & AGENDA', {
            'fields': (
                'agenda', 'objectives', 'description'
            )
        }),

        ('✅ STATUS & TRACKING', {
            'fields': (
                'status', 'meeting_minutes', 'decisions_made', 'action_items',
                'next_meeting_date'
            )
        }),

        ('👥 ATTENDANCE', {
            'fields': (
                'expected_attendees', 'actual_attendees', 'attendance_sheet',
                'attendance_analysis_display'
            )
        }),

        ('🔔 REMINDERS', {
            'fields': (
                'send_reminder', 'reminder_sent', 'reminder_sent_date'
            )
        }),

        ('📊 MEETING DETAILS', {
            'fields': (
                'meeting_details_display',
            )
        }),

        ('👤 AUDIT INFORMATION', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            )
        }),
    )

    def meeting_type_display(self, obj):
        type_map = {
            'group_meeting': '👥 Group Meeting',
            'loan_committee': '💳 Loan Committee',
            'board_meeting': '🏢 Board Meeting',
            'training': '🎓 Training',
            'field_visit': '🌍 Field Visit',
            'other': '📄 Other',
        }
        return type_map.get(obj.meeting_type, obj.get_meeting_type_display())
    meeting_type_display.short_description = 'Type'

    def group_link(self, obj):
        if obj.group:
            url = reverse('admin:groups_group_change', args=[obj.group.id])
            return format_html('<a href="{}">{}</a>', url, obj.group.name)
        return "N/A"
    group_link.short_description = 'Group'

    def officer_link(self, obj):
        url = reverse('admin:users_customuser_change', args=[obj.officer.id])
        return format_html('<a href="{}">{}</a>', url, obj.officer.get_full_name())
    officer_link.short_description = 'Officer'

    def status_display(self, obj):
        status_map = {
            'scheduled': '🟡 Scheduled',
            'ongoing': '🟠 Ongoing',
            'completed': '✅ Completed',
            'cancelled': '❌ Cancelled',
            'postponed': '↩️ Postponed',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'

    def attendance_rate_display(self, obj):
        rate = obj.attendance_rate
        if rate >= 80:
            color = 'green'
            icon = '✅'
        elif rate >= 60:
            color = 'orange'
            icon = '⚠️'
        else:
            color = 'red'
            icon = '❌'

        return format_html(
            '<span style="color: {};">{} {}%</span>',
            color, icon, round(rate, 1)
        )
    attendance_rate_display.short_description = 'Attendance'

    def is_upcoming_display(self, obj):
        if obj.is_today:
            return format_html('🟢 Today')
        elif obj.is_upcoming:
            return format_html('🟡 Upcoming')
        else:
            return format_html('⚪ Past')
    is_upcoming_display.short_description = 'Timing'

    def meeting_details_display(self, obj):
        html = f"""
        <div style="background: #d4edda; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb;">
            <h4 style="margin-top: 0; color: #155724;">📊 Meeting Details</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div><strong>Meeting ID:</strong> {obj.meeting_id}</div>
                <div><strong>Type:</strong> {obj.get_meeting_type_display()}</div>
                <div><strong>Date:</strong> {obj.scheduled_date}</div>
                <div><strong>Time:</strong> {obj.scheduled_time}</div>
                <div><strong>Duration:</strong> {obj.expected_duration} min</div>
                <div><strong>Status:</strong> {obj.get_status_display()}</div>
                <div><strong>Venue:</strong> {obj.venue}</div>
                <div><strong>Group:</strong> {obj.group.name if obj.group else 'N/A'}</div>
            </div>
        </div>
        """
        return format_html(html)
    meeting_details_display.short_description = 'Meeting Details'

    def attendance_analysis_display(self, obj):
        html = f"""
        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border: 1px solid #ffeaa7;">
            <h4 style="margin-top: 0; color: #856404;">👥 Attendance Analysis</h4>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                <div style="background: #d4edda; padding: 10px; border-radius: 3px;">
                    <strong>Expected:</strong><br>
                    <span style="font-size: 16px; font-weight: bold;">{obj.expected_attendees}</span>
                </div>

                <div style="background: #cce7ff; padding: 10px; border-radius: 3px;">
                    <strong>Actual:</strong><br>
                    <span style="font-size: 16px; font-weight: bold;">{obj.actual_attendees}</span>
                </div>
            </div>

            <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
                <div style="background: {'green' if obj.attendance_rate >= 80 else 'orange' if obj.attendance_rate >= 60 else 'red'};
                            height: 100%; width: {min(obj.attendance_rate, 100)}%;"></div>
            </div>

            <div style="text-align: center; font-weight: bold;">
                Attendance Rate: {obj.attendance_rate:.1f}%
            </div>
        </div>
        """
        return format_html(html)
    attendance_analysis_display.short_description = 'Attendance Analysis'

@admin.register(FieldVisit)
class FieldVisitAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Filter field visits based on user type
        if request.user.user_type == 'field_officer':
            # Field officers can only see field visits for groups assigned to them
            qs = qs.filter(group__field_officer=request.user)
        # Admin users can see all field visits

        return qs
    list_display = [
        'visit_id', 'visit_type_display', 'scheduled_date', 'group_link',
        'officer_link', 'status_display', 'members_met_count', 'is_completed_display'
    ]

    list_filter = [
        'visit_type', 'status', 'scheduled_date', 'officer', 'group'
    ]

    search_fields = [
        'visit_id', 'group__name', 'officer__username', 'purpose', 'location'
    ]

    readonly_fields = [
        'visit_id', 'created_at', 'updated_at'
    ]

    filter_horizontal = ['accompanying_staff', 'members_met']

    def visit_type_display(self, obj):
        type_map = {
            'routine': '🔄 Routine',
            'loan_followup': '💳 Loan Follow-up',
            'savings_mobilization': '💰 Savings Mobilization',
            'problem_resolution': '🔧 Problem Resolution',
            'training': '🎓 Training',
            'other': '📄 Other',
        }
        return type_map.get(obj.visit_type, obj.get_visit_type_display())
    visit_type_display.short_description = 'Type'

    def group_link(self, obj):
        url = reverse('admin:groups_group_change', args=[obj.group.id])
        return format_html('<a href="{}">{}</a>', url, obj.group.name)
    group_link.short_description = 'Group'

    def officer_link(self, obj):
        url = reverse('admin:users_customuser_change', args=[obj.officer.id])
        return format_html('<a href="{}">{}</a>', url, obj.officer.get_full_name())
    officer_link.short_description = 'Officer'

    def status_display(self, obj):
        status_map = {
            'scheduled': '🟡 Scheduled',
            'in_progress': '🟠 In Progress',
            'completed': '✅ Completed',
            'cancelled': '❌ Cancelled',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'

    def is_completed_display(self, obj):
        if obj.is_completed:
            return format_html('✅ Completed')
        elif obj.is_overdue:
            return format_html('🔴 Overdue')
        else:
            return format_html('🟡 Scheduled')
    is_completed_display.short_description = 'Completion'

@admin.register(OfficerPerformance)
class OfficerPerformanceAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Filter officer performance based on user type
        if request.user.user_type == 'field_officer':
            # Field officers can only see their own performance records
            qs = qs.filter(officer=request.user)
        # Admin users can see all officer performance records

        return qs
    list_display = [
        'officer_link', 'performance_date', 'period_type_display',
        'performance_score_display', 'meetings_completion_rate_display',
        'visits_completion_rate_display', 'loan_recovery_rate_display'
    ]

    list_filter = [
        'period_type', 'performance_date', 'officer'
    ]

    search_fields = [
        'officer__username', 'officer__first_name', 'officer__last_name'
    ]

    readonly_fields = [
        'meetings_completion_rate', 'visits_completion_rate', 'groups_visit_rate',
        'savings_target_achievement', 'loans_target_achievement'
    ]

    def officer_link(self, obj):
        url = reverse('admin:users_customuser_change', args=[obj.officer.id])
        return format_html('<a href="{}">{}</a>', url, obj.officer.get_full_name())
    officer_link.short_description = 'Officer'

    def period_type_display(self, obj):
        type_map = {
            'daily': '📅 Daily',
            'weekly': '📅 Weekly',
            'monthly': '📅 Monthly',
            'quarterly': '📅 Quarterly',
            'yearly': '📅 Yearly',
        }
        return type_map.get(obj.period_type, obj.get_period_type_display())
    period_type_display.short_description = 'Period'

    def performance_score_display(self, obj):
        if obj.performance_score >= 80:
            color = 'green'
            status = 'Excellent'
        elif obj.performance_score >= 60:
            color = 'orange'
            status = 'Good'
        elif obj.performance_score >= 40:
            color = 'red'
            status = 'Poor'
        else:
            color = 'darkred'
            status = 'Very Poor'

        return format_html(
            '<span style="color: {};">{}% ({})</span>',
            color, obj.performance_score, status
        )
    performance_score_display.short_description = 'Performance'

    def meetings_completion_rate_display(self, obj):
        rate = obj.meetings_completion_rate
        color = 'green' if rate >= 80 else 'orange' if rate >= 60 else 'red'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, round(rate, 1)
        )
    meetings_completion_rate_display.short_description = 'Meetings'

    def visits_completion_rate_display(self, obj):
        rate = obj.visits_completion_rate
        color = 'green' if rate >= 80 else 'orange' if rate >= 60 else 'red'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, round(rate, 1)
        )
    visits_completion_rate_display.short_description = 'Visits'

    def loan_recovery_rate_display(self, obj):
        rate = obj.loan_recovery_rate
        color = 'green' if rate >= 90 else 'orange' if rate >= 75 else 'red'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, round(rate, 1)
        )
    loan_recovery_rate_display.short_description = 'Loan Recovery'

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'widget_type_display', 'title', 'is_active_display',
        'is_default_display', 'display_order'
    ]

    list_filter = ['widget_type', 'is_active', 'is_default']

    search_fields = ['name', 'title', 'description']

    def widget_type_display(self, obj):
        type_map = {
            'statistic': '📊 Statistic',
            'chart': '📈 Chart',
            'list': '📋 List',
            'calendar': '📅 Calendar',
            'progress': '📊 Progress',
            'alert': '⚠️ Alert',
        }
        return type_map.get(obj.widget_type, obj.get_widget_type_display())
    widget_type_display.short_description = 'Type'

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('✅ Active')
        return format_html('❌ Inactive')
    is_active_display.short_description = 'Active'

    def is_default_display(self, obj):
        if obj.is_default:
            return format_html('⭐ Default')
        return format_html('⚪ Custom')
    is_default_display.short_description = 'Default'

@admin.register(OfficerAlert)
class OfficerAlertAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Filter officer alerts based on user type
        if request.user.user_type == 'field_officer':
            # Field officers can only see their own alerts
            qs = qs.filter(officer=request.user)
        # Admin users can see all officer alerts

        return qs
    list_display = [
        'title', 'officer_link', 'alert_type_display', 'alert_level_display',
        'is_active_display', 'alert_date'
    ]

    list_filter = ['alert_type', 'alert_level', 'is_read', 'is_dismissed', 'alert_date']

    search_fields = ['title', 'message', 'officer__username']

    readonly_fields = ['alert_date', 'read_date', 'dismiss_date']

    def officer_link(self, obj):
        url = reverse('admin:users_customuser_change', args=[obj.officer.id])
        return format_html('<a href="{}">{}</a>', url, obj.officer.get_full_name())
    officer_link.short_description = 'Officer'

    def alert_type_display(self, obj):
        type_map = {
            'meeting_reminder': '📅 Meeting Reminder',
            'visit_reminder': '🌍 Visit Reminder',
            'loan_overdue': '💳 Loan Overdue',
            'performance': '📊 Performance',
            'system': '⚙️ System',
            'other': '📄 Other',
        }
        return type_map.get(obj.alert_type, obj.get_alert_type_display())
    alert_type_display.short_description = 'Type'

    def alert_level_display(self, obj):
        level_map = {
            'low': '🟢 Low',
            'medium': '🟡 Medium',
            'high': '🟠 High',
            'critical': '🔴 Critical',
        }
        return level_map.get(obj.alert_level, obj.get_alert_level_display())
    alert_level_display.short_description = 'Level'

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('🔴 Active')
        return format_html('⚪ Inactive')
        if obj.is_active:
            return format_html('🔴 Active')
        return format_html('⚪ Inactive')
    is_active_display.short_description = 'Active'

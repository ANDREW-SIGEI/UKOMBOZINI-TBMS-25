from rest_framework import serializers
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import MeetingSchedule, FieldVisit, OfficerPerformance, DashboardWidget, OfficerAlert, Event, EventAttendance

class MeetingScheduleSerializer(serializers.ModelSerializer):
    officer_name = serializers.CharField(source='officer.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    attendance_rate = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    is_today = serializers.SerializerMethodField()

    class Meta:
        model = MeetingSchedule
        fields = [
            'id', 'meeting_id', 'title', 'meeting_type', 'scheduled_date',
            'scheduled_time', 'expected_duration', 'venue', 'venue_address',
            'gps_coordinates', 'group', 'group_name', 'officer', 'officer_name',
            'agenda', 'objectives', 'description', 'status', 'actual_start_time',
            'actual_end_time', 'actual_duration', 'expected_attendees',
            'actual_attendees', 'attendance_sheet', 'meeting_minutes',
            'decisions_made', 'action_items', 'next_meeting_date',
            'send_reminder', 'reminder_sent', 'reminder_sent_date',
            'created_by', 'created_by_name', 'attendance_rate', 'is_upcoming',
            'is_today', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'meeting_id', 'created_at', 'updated_at', 'attendance_rate',
            'is_upcoming', 'is_today'
        ]

    def get_attendance_rate(self, obj):
        return obj.attendance_rate

    def get_is_upcoming(self, obj):
        return obj.is_upcoming

    def get_is_today(self, obj):
        return obj.is_today

    def validate(self, attrs):
        # Validate scheduled date
        scheduled_date = attrs.get('scheduled_date')
        if scheduled_date and scheduled_date < date.today():
            raise serializers.ValidationError({
                'scheduled_date': 'Meeting date cannot be in the past'
            })

        return attrs

class FieldVisitSerializer(serializers.ModelSerializer):
    officer_name = serializers.CharField(source='officer.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    members_met_names = serializers.SerializerMethodField()
    accompanying_staff_names = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = FieldVisit
        fields = [
            'id', 'visit_id', 'visit_type', 'scheduled_date', 'scheduled_time',
            'actual_date', 'actual_time', 'group', 'group_name', 'location',
            'gps_coordinates', 'officer', 'officer_name', 'accompanying_staff',
            'accompanying_staff_names', 'purpose', 'objectives', 'expected_outcomes',
            'status', 'visit_report', 'findings', 'recommendations', 'action_items',
            'members_met', 'members_met_names', 'members_met_count', 'photos',
            'supporting_documents', 'requires_followup', 'followup_date',
            'followup_actions', 'is_completed', 'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'visit_id', 'members_met_count', 'created_at', 'updated_at',
            'is_completed', 'is_overdue'
        ]

    def get_members_met_names(self, obj):
        return [member.get_full_name() for member in obj.members_met.all()]

    def get_accompanying_staff_names(self, obj):
        return [staff.get_full_name() for staff in obj.accompanying_staff.all()]

    def get_is_completed(self, obj):
        return obj.is_completed

    def get_is_overdue(self, obj):
        return obj.is_overdue

class OfficerPerformanceSerializer(serializers.ModelSerializer):
    officer_name = serializers.CharField(source='officer.get_full_name', read_only=True)
    meetings_completion_rate = serializers.SerializerMethodField()
    visits_completion_rate = serializers.SerializerMethodField()
    groups_visit_rate = serializers.SerializerMethodField()
    savings_target_achievement = serializers.SerializerMethodField()
    loans_target_achievement = serializers.SerializerMethodField()

    class Meta:
        model = OfficerPerformance
        fields = [
            'id', 'officer', 'officer_name', 'performance_date', 'period_type',
            'meetings_scheduled', 'meetings_completed', 'meetings_cancelled',
            'average_attendance_rate', 'visits_scheduled', 'visits_completed',
            'visits_cancelled', 'total_members_met', 'groups_assigned',
            'groups_visited', 'groups_active', 'total_savings_mobilized',
            'total_loans_disbursed', 'total_repayments_collected', 'loan_recovery_rate',
            'performance_score', 'productivity_score', 'efficiency_score',
            'meetings_target', 'visits_target', 'savings_target', 'loans_target',
            'meetings_completion_rate', 'visits_completion_rate', 'groups_visit_rate',
            'savings_target_achievement', 'loans_target_achievement'
        ]
        read_only_fields = [
            'id', 'meetings_completion_rate', 'visits_completion_rate',
            'groups_visit_rate', 'savings_target_achievement', 'loans_target_achievement'
        ]

    def get_meetings_completion_rate(self, obj):
        return obj.meetings_completion_rate

    def get_visits_completion_rate(self, obj):
        return obj.visits_completion_rate

    def get_groups_visit_rate(self, obj):
        return obj.groups_visit_rate

    def get_savings_target_achievement(self, obj):
        return obj.savings_target_achievement

    def get_loans_target_achievement(self, obj):
        return obj.loans_target_achievement

class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'name', 'widget_type', 'chart_type', 'data_source', 'filters',
            'refresh_interval', 'title', 'description', 'icon', 'color', 'column',
            'row', 'width', 'height', 'is_active', 'is_default', 'user_roles',
            'display_order'
        ]

class OfficerAlertSerializer(serializers.ModelSerializer):
    officer_name = serializers.CharField(source='officer.get_full_name', read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = OfficerAlert
        fields = [
            'id', 'officer', 'officer_name', 'alert_type', 'alert_level',
            'title', 'message', 'related_object_type', 'related_object_id',
            'is_read', 'is_dismissed', 'action_required', 'action_taken',
            'alert_date', 'read_date', 'dismiss_date', 'expiry_date', 'is_active'
        ]
        read_only_fields = ['id', 'alert_date', 'is_active']

    def get_is_active(self, obj):
        return obj.is_active

class DashboardOverviewSerializer(serializers.Serializer):
    # Meeting Statistics
    total_meetings = serializers.IntegerField()
    meetings_today = serializers.IntegerField()
    meetings_this_week = serializers.IntegerField()
    upcoming_meetings = serializers.IntegerField()

    # Field Visit Statistics
    total_visits = serializers.IntegerField()
    visits_this_week = serializers.IntegerField()
    overdue_visits = serializers.IntegerField()
    visits_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    # Group Statistics
    total_groups = serializers.IntegerField()
    groups_visited_this_month = serializers.IntegerField()
    groups_visit_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    # Financial Statistics
    total_savings = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_loans = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_repayments = serializers.DecimalField(max_digits=12, decimal_places=2)
    loan_recovery_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    # Performance Statistics
    performance_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    productivity_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    efficiency_score = serializers.DecimalField(max_digits=5, decimal_places=2)

    # Alerts
    active_alerts = serializers.IntegerField()
    high_priority_alerts = serializers.IntegerField()

class CalendarEventSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    type = serializers.CharField()
    color = serializers.CharField()
    description = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    status = serializers.CharField(required=False)

class EventSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    duration_hours = serializers.ReadOnlyField()
    attendance_rate = serializers.ReadOnlyField()
    attendee_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'start_datetime', 'end_datetime',
            'venue', 'venue_address', 'gps_coordinates', 'group', 'group_name',
            'created_by', 'created_by_name', 'status', 'expected_attendees',
            'actual_attendees', 'notes', 'action_items', 'duration_hours',
            'attendance_rate', 'attendee_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'duration_hours', 'attendance_rate']

    def get_attendee_count(self, obj):
        return obj.attendees.count()

class EventAttendanceSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    duration_attended = serializers.ReadOnlyField()

    class Meta:
        model = EventAttendance
        fields = [
            'id', 'event', 'event_title', 'member', 'member_name', 'status',
            'arrival_time', 'departure_time', 'contribution_amount', 'notes',
            'recorded_by', 'recorded_by_name', 'recorded_at', 'duration_attended'
        ]
        read_only_fields = ['recorded_at', 'duration_attended']

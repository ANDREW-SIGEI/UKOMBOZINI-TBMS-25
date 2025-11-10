from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from datetime import date, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from ukombozini.apps.sync.models import SyncableModel

User = get_user_model()

class MeetingSchedule(SyncableModel):
    MEETING_TYPES = (
        ('group_meeting', 'Group Meeting'),
        ('loan_committee', 'Loan Committee Meeting'),
        ('board_meeting', 'Board Meeting'),
        ('training', 'Training Session'),
        ('field_visit', 'Field Visit'),
        ('other', 'Other Meeting'),
    )

    MEETING_STATUS = (
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    )

    # Basic Information
    meeting_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    title = models.CharField(max_length=200)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, default='group_meeting')

    # Scheduling
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    expected_duration = models.PositiveIntegerField(
        default=60,  # minutes
        validators=[MinValueValidator(15), MaxValueValidator(480)],
        verbose_name="Expected Duration (minutes)"
    )

    # Location
    venue = models.CharField(max_length=200)
    venue_address = models.TextField(blank=True, null=True)
    gps_coordinates = models.CharField(max_length=100, blank=True, null=True, verbose_name="GPS Coordinates")

    # Organization
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='scheduled_meetings',
        null=True,
        blank=True
    )
    officer = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='scheduled_meetings'
    )

    # Agenda and Description
    agenda = models.TextField(blank=True, null=True)
    objectives = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Status and Tracking
    status = models.CharField(max_length=20, choices=MEETING_STATUS, default='scheduled')
    actual_start_time = models.DateTimeField(blank=True, null=True)
    actual_end_time = models.DateTimeField(blank=True, null=True)
    actual_duration = models.PositiveIntegerField(blank=True, null=True, verbose_name="Actual Duration (minutes)")

    # Attendance
    expected_attendees = models.PositiveIntegerField(default=0)
    actual_attendees = models.PositiveIntegerField(default=0)
    attendance_sheet = models.FileField(
        upload_to='meeting_attendance/',
        blank=True,
        null=True,
        verbose_name="Attendance Sheet"
    )

    # Outcomes
    meeting_minutes = models.TextField(blank=True, null=True)
    decisions_made = models.TextField(blank=True, null=True)
    action_items = models.TextField(blank=True, null=True)
    next_meeting_date = models.DateField(blank=True, null=True)

    # Reminders and Notifications
    send_reminder = models.BooleanField(default=True)
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_date = models.DateTimeField(blank=True, null=True)

    # Audit Fields
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_meetings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Meeting Schedule'
        verbose_name_plural = 'Meeting Schedules'
        ordering = ['scheduled_date', 'scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['officer', 'scheduled_date']),
            models.Index(fields=['group', 'scheduled_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.scheduled_date} {self.scheduled_time}"

    def save(self, *args, **kwargs):
        # Generate meeting ID if not set
        if not self.meeting_id:
            self.meeting_id = f"MT{uuid.uuid4().hex[:8].upper()}"

        # Calculate actual duration if start and end times are provided
        if self.actual_start_time and self.actual_end_time:
            duration = self.actual_end_time - self.actual_start_time
            self.actual_duration = duration.total_seconds() // 60

        super().save(*args, **kwargs)

    def clean(self):
        """Validate meeting data"""
        if self.scheduled_date < date.today():
            raise ValidationError({
                'scheduled_date': 'Meeting date cannot be in the past'
            })

        if self.actual_start_time and self.actual_end_time:
            if self.actual_end_time <= self.actual_start_time:
                raise ValidationError({'actual_end_time': 'End time must be after start time'})

    @property
    def is_upcoming(self):
        """Check if meeting is upcoming (within next 7 days)"""
        today = date.today()
        return self.scheduled_date >= today and self.scheduled_date <= today + timedelta(days=7)

    @property
    def is_today(self):
        """Check if meeting is scheduled for today"""
        return self.scheduled_date == date.today()

    @property
    def attendance_rate(self):
        """Calculate attendance rate"""
        if self.expected_attendees > 0:
            return (self.actual_attendees / self.expected_attendees) * 100
        return 0

class FieldVisit(SyncableModel):
    VISIT_TYPES = (
        ('routine', 'Routine Visit'),
        ('loan_followup', 'Loan Follow-up'),
        ('savings_mobilization', 'Savings Mobilization'),
        ('problem_resolution', 'Problem Resolution'),
        ('training', 'Training Visit'),
        ('other', 'Other'),
    )

    VISIT_STATUS = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    # Basic Information
    visit_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    visit_type = models.CharField(max_length=30, choices=VISIT_TYPES, default='routine')

    # Scheduling
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    actual_date = models.DateField(blank=True, null=True)
    actual_time = models.TimeField(blank=True, null=True)

    # Location
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='field_visits')
    location = models.CharField(max_length=200)
    gps_coordinates = models.CharField(max_length=100, blank=True, null=True, verbose_name="GPS Coordinates")

    # Officer Information
    officer = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='field_visits')
    accompanying_staff = models.ManyToManyField(
        'users.CustomUser',
        blank=True,
        related_name='accompanied_visits'
    )

    # Purpose and Objectives
    purpose = models.TextField()
    objectives = models.TextField(blank=True, null=True)
    expected_outcomes = models.TextField(blank=True, null=True)

    # Status and Tracking
    status = models.CharField(max_length=20, choices=VISIT_STATUS, default='scheduled')
    visit_report = models.TextField(blank=True, null=True)
    findings = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)
    action_items = models.TextField(blank=True, null=True)

    # Attendance and Participation
    members_met = models.ManyToManyField(
        'members.Member',
        blank=True,
        related_name='field_visits_attended'
    )
    members_met_count = models.PositiveIntegerField(default=0)

    # Documentation
    photos = models.FileField(
        upload_to='field_visit_photos/',
        blank=True,
        null=True,
        verbose_name="Visit Photos"
    )
    supporting_documents = models.FileField(
        upload_to='field_visit_docs/',
        blank=True,
        null=True,
        verbose_name="Supporting Documents"
    )

    # Follow-up
    requires_followup = models.BooleanField(default=False)
    followup_date = models.DateField(blank=True, null=True)
    followup_actions = models.TextField(blank=True, null=True)

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Field Visit'
        verbose_name_plural = 'Field Visits'
        ordering = ['-scheduled_date', '-scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['officer', 'scheduled_date']),
            models.Index(fields=['group', 'scheduled_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Field Visit - {self.group.name} - {self.scheduled_date}"

    def save(self, *args, **kwargs):
        # Generate visit ID if not set
        if not self.visit_id:
            self.visit_id = f"FV{uuid.uuid4().hex[:8].upper()}"

        # Update members met count
        if self.pk:
            self.members_met_count = self.members_met.count()

        super().save(*args, **kwargs)

    @property
    def is_completed(self):
        """Check if visit is completed"""
        return self.status == 'completed'

    @property
    def is_overdue(self):
        """Check if scheduled visit is overdue"""
        return self.status == 'scheduled' and self.scheduled_date < date.today()

class OfficerPerformance(models.Model):
    """Track officer performance metrics"""

    officer = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='performance_metrics')
    performance_date = models.DateField(default=date.today)
    period_type = models.CharField(
        max_length=10,
        choices=(
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ),
        default='monthly'
    )

    # Meeting Metrics
    meetings_scheduled = models.PositiveIntegerField(default=0)
    meetings_completed = models.PositiveIntegerField(default=0)
    meetings_cancelled = models.PositiveIntegerField(default=0)
    average_attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Field Visit Metrics
    visits_scheduled = models.PositiveIntegerField(default=0)
    visits_completed = models.PositiveIntegerField(default=0)
    visits_cancelled = models.PositiveIntegerField(default=0)
    total_members_met = models.PositiveIntegerField(default=0)

    # Group Management Metrics
    groups_assigned = models.PositiveIntegerField(default=0)
    groups_visited = models.PositiveIntegerField(default=0)
    groups_active = models.PositiveIntegerField(default=0)

    # Financial Metrics
    total_savings_mobilized = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_loans_disbursed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_repayments_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_recovery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Performance Scores
    performance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    productivity_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    efficiency_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Targets vs Actuals
    meetings_target = models.PositiveIntegerField(default=0)
    visits_target = models.PositiveIntegerField(default=0)
    savings_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loans_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Officer Performance'
        verbose_name_plural = 'Officer Performance Metrics'
        ordering = ['-performance_date', 'officer']
        unique_together = ['officer', 'performance_date', 'period_type']
        indexes = [
            models.Index(fields=['officer', 'performance_date']),
            models.Index(fields=['performance_date', 'period_type']),
        ]

    def __str__(self):
        return f"Performance - {self.officer.get_full_name()} - {self.performance_date}"

    @property
    def meetings_completion_rate(self):
        """Calculate meetings completion rate"""
        if self.meetings_scheduled > 0:
            return (self.meetings_completed / self.meetings_scheduled) * 100
        return 0

    @property
    def visits_completion_rate(self):
        """Calculate visits completion rate"""
        if self.visits_scheduled > 0:
            return (self.visits_completed / self.visits_scheduled) * 100
        return 0

    @property
    def groups_visit_rate(self):
        """Calculate groups visit rate"""
        if self.groups_assigned > 0:
            return (self.groups_visited / self.groups_assigned) * 100
        return 0

    @property
    def savings_target_achievement(self):
        """Calculate savings target achievement"""
        if self.savings_target > 0:
            return (self.total_savings_mobilized / self.savings_target) * 100
        return 0

    @property
    def loans_target_achievement(self):
        """Calculate loans target achievement"""
        if self.loans_target > 0:
            return (self.total_loans_disbursed / self.loans_target) * 100
        return 0

class DashboardWidget(models.Model):
    """Configurable dashboard widgets for officers"""

    WIDGET_TYPES = (
        ('statistic', 'Statistic Card'),
        ('chart', 'Chart'),
        ('list', 'List'),
        ('calendar', 'Calendar'),
        ('progress', 'Progress Bar'),
        ('alert', 'Alert Box'),
    )

    CHART_TYPES = (
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('radar', 'Radar Chart'),
    )

    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, blank=True, null=True)

    # Configuration
    data_source = models.CharField(max_length=100, help_text="Model or function to get data from")
    filters = models.JSONField(blank=True, null=True, help_text="JSON filters for data")
    refresh_interval = models.PositiveIntegerField(default=300, help_text="Refresh interval in seconds")

    # Display
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, default='primary')

    # Position and Size
    column = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(4)])
    row = models.PositiveIntegerField(default=1)
    width = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(4)])
    height = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(4)])

    # Visibility
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    user_roles = models.JSONField(
        blank=True,
        null=True,
        help_text="JSON list of user roles that can see this widget"
    )

    # Order
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Dashboard Widget'
        verbose_name_plural = 'Dashboard Widgets'
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"

class OfficerAlert(models.Model):
    """Alert system for officers"""

    ALERT_TYPES = (
        ('meeting_reminder', 'Meeting Reminder'),
        ('visit_reminder', 'Field Visit Reminder'),
        ('event_reminder', 'Event Reminder'),
        ('loan_overdue', 'Loan Overdue Alert'),
        ('savings_target', 'Savings Target Alert'),
        ('performance', 'Performance Alert'),
        ('system', 'System Alert'),
        ('other', 'Other Alert'),
    )

    ALERT_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )

    officer = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    alert_level = models.CharField(max_length=10, choices=ALERT_LEVELS, default='medium')

    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.PositiveIntegerField(blank=True, null=True)

    # Status
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    action_required = models.BooleanField(default=False)
    action_taken = models.BooleanField(default=False)

    # Timing
    alert_date = models.DateTimeField(auto_now_add=True)
    read_date = models.DateTimeField(blank=True, null=True)
    dismiss_date = models.DateTimeField(blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Officer Alert'
        verbose_name_plural = 'Officer Alerts'
        ordering = ['-alert_date']
        indexes = [
            models.Index(fields=['officer', 'is_read']),
            models.Index(fields=['alert_date']),
        ]

    def __str__(self):
        return f"{self.get_alert_level_display()} - {self.title} - {self.officer.get_full_name()}"

    @property
    def is_active(self):
        """Check if alert is still active"""
        if self.is_dismissed or self.is_read and not self.action_required:
            return False
        if self.expiry_date and self.expiry_date < timezone.now():
            return False
        return True

    def mark_as_read(self):
        """Mark alert as read"""
        self.is_read = True
        self.read_date = timezone.now()
        self.save()

    def dismiss(self):
        """Dismiss alert"""
        self.is_dismissed = True
        self.dismiss_date = timezone.now()
        self.save()

class Event(SyncableModel):
    """General Event model for calendar and attendance tracking"""

    EVENT_TYPES = (
        ('meeting', 'Meeting'),
        ('training', 'Training'),
        ('workshop', 'Workshop'),
        ('field_visit', 'Field Visit'),
        ('ceremony', 'Ceremony'),
        ('other', 'Other'),
    )

    EVENT_STATUS = (
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    )

    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='meeting')

    # Scheduling
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    # Location
    venue = models.CharField(max_length=200)
    venue_address = models.TextField(blank=True, null=True)
    gps_coordinates = models.CharField(max_length=100, blank=True, null=True)

    # Organization
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='events'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events'
    )

    # Attendees (Many-to-Many through Attendance)
    attendees = models.ManyToManyField(
        'members.Member',
        through='EventAttendance',
        related_name='attended_events',
        blank=True
    )

    # Status and Tracking
    status = models.CharField(max_length=20, choices=EVENT_STATUS, default='scheduled')
    expected_attendees = models.PositiveIntegerField(default=0)
    actual_attendees = models.PositiveIntegerField(default=0)

    # Outcomes and Notes
    notes = models.TextField(blank=True, null=True)
    action_items = models.TextField(blank=True, null=True)

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['start_datetime']),
            models.Index(fields=['group', 'start_datetime']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"

    def clean(self):
        """Validate event data"""
        if self.end_datetime <= self.start_datetime:
            raise ValidationError({
                'end_datetime': 'End datetime must be after start datetime'
            })

    @property
    def duration_hours(self):
        """Calculate event duration in hours"""
        duration = self.end_datetime - self.start_datetime
        return duration.total_seconds() / 3600

    @property
    def attendance_rate(self):
        """Calculate attendance rate"""
        if self.expected_attendees > 0:
            return (self.actual_attendees / self.expected_attendees) * 100
        return 0

    @property
    def is_upcoming(self):
        """Check if event is upcoming (within next 7 days)"""
        now = timezone.now()
        return self.start_datetime >= now and self.start_datetime <= now + timedelta(days=7)

    @property
    def is_today(self):
        """Check if event is scheduled for today"""
        return self.start_datetime.date() == date.today()

class EventAttendance(SyncableModel):
    """Attendance record for events"""

    ATTENDANCE_STATUS = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendance_records')
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='event_attendance')

    # Attendance Details
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS, default='present')
    arrival_time = models.DateTimeField(blank=True, null=True)
    departure_time = models.DateTimeField(blank=True, null=True)

    # Contributions/Notes
    contribution_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    notes = models.TextField(blank=True, null=True)

    # Audit
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_attendance'
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Event Attendance'
        verbose_name_plural = 'Event Attendance'
        unique_together = ['event', 'member']
        ordering = ['event', 'member']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['member', 'event']),
        ]

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.event.title} - {self.get_status_display()}"

    @property
    def duration_attended(self):
        """Calculate duration attended"""
        if self.arrival_time and self.departure_time:
            duration = self.departure_time - self.arrival_time
            return duration.total_seconds() / 3600  # hours
        return 0


class AuditLog(models.Model):
    """Comprehensive audit logging for system activities"""

    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('bulk_update', 'Bulk Update'),
        ('other', 'Other'),
    )

    # Actor Information
    actor = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        help_text="User who performed the action"
    )

    # Action Details
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_type = models.CharField(max_length=50, help_text="Model name of the target object")
    target_id = models.PositiveIntegerField(help_text="ID of the target object")

    # Data Changes
    old_value = models.JSONField(blank=True, null=True, help_text="Previous state as JSON")
    new_value = models.JSONField(blank=True, null=True, help_text="New state as JSON")

    # Context
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="GPS coordinates (lat,long) if available"
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    # Additional Metadata
    description = models.TextField(blank=True, null=True, help_text="Human-readable description")
    session_id = models.CharField(max_length=100, blank=True, null=True)
    request_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        actor_name = self.actor.get_full_name() if self.actor else 'System'
        return f"{actor_name} - {self.get_action_type_display()} - {self.target_type} #{self.target_id} - {self.timestamp}"

    @classmethod
    def log_action(cls, actor, action_type, target_type, target_id,
                   old_value=None, new_value=None, description=None,
                   location=None, ip_address=None, user_agent=None,
                   session_id=None, request_id=None):
        """Convenience method to create audit log entries"""
        return cls.objects.create(
            actor=actor,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            description=description,
            location=location,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id
        )

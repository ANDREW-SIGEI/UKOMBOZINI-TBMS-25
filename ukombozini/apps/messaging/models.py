from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone
from ukombozini.apps.sync.models import SyncableModel

class Message(SyncableModel):
    """Store sent messages to members"""

    MESSAGE_TYPES = (
        ('loan_balance', 'Loan Balance Update'),
        ('meeting_notification', 'Meeting Notification'),
        ('meeting_reminder', 'Meeting Reminder'),
        ('visit_reminder', 'Field Visit Reminder'),
        ('savings_update', 'Savings Update'),
        ('general', 'General Message'),
    )

    MESSAGE_STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    )

    DELIVERY_METHODS = (
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('both', 'SMS and Email'),
    )

    # Basic Information
    message_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHODS, default='sms')

    # Recipients
    recipient = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='received_messages')
    recipient_phone = models.CharField(max_length=15, blank=True, null=True)
    recipient_email = models.EmailField(blank=True, null=True)

    # Content
    subject = models.CharField(max_length=200, blank=True, null=True)
    message_body = models.TextField()

    # Related Objects
    related_group = models.ForeignKey('groups.Group', on_delete=models.SET_NULL, blank=True, null=True)
    related_loan = models.ForeignKey('loans.Loan', on_delete=models.SET_NULL, blank=True, null=True)
    related_meeting = models.ForeignKey('dashboard.MeetingSchedule', on_delete=models.SET_NULL, blank=True, null=True)
    related_field_visit = models.ForeignKey('dashboard.FieldVisit', on_delete=models.SET_NULL, blank=True, null=True)

    # Status and Tracking
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS, default='pending')
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)

    # Error handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.PositiveIntegerField(default=0)

    # Provider details (for SMS gateway)
    provider_reference = models.CharField(max_length=100, blank=True, null=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Audit
    sent_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['message_type', 'status']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return f"{self.get_message_type_display()} to {self.recipient.get_full_name()} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Generate message ID if not set
        if not self.message_id:
            self.message_id = f"MSG{uuid.uuid4().hex[:8].upper()}"

        # Set timestamps based on status
        if self.status == 'sent' and not self.sent_at:
            self.sent_at = timezone.now()
        elif self.status == 'delivered' and not self.delivered_at:
            self.delivered_at = timezone.now()
        elif self.status == 'failed' and not self.failed_at:
            self.failed_at = timezone.now()

        super().save(*args, **kwargs)

    def mark_as_sent(self, provider_ref=None, cost=0):
        """Mark message as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if provider_ref:
            self.provider_reference = provider_ref
        if cost:
            self.cost = cost
        self.save()

    def mark_as_delivered(self):
        """Mark message as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()

    def mark_as_failed(self, error_message=None):
        """Mark message as failed"""
        self.status = 'failed'
        self.failed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        self.retry_count += 1
        self.save()

class MessageTemplate(models.Model):
    """Templates for different types of messages"""

    TEMPLATE_TYPES = (
        ('loan_balance', 'Loan Balance Update'),
        ('meeting_notification', 'Meeting Notification'),
        ('savings_update', 'Savings Update'),
        ('welcome', 'Welcome Message'),
        ('reminder', 'Reminder'),
    )

    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    subject_template = models.CharField(max_length=200, blank=True, null=True)
    message_template = models.TextField()

    # Variables available in template
    available_variables = models.JSONField(
        blank=True,
        null=True,
        help_text="JSON list of available variables for this template"
    )

    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Audit
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Message Template'
        verbose_name_plural = 'Message Templates'
        ordering = ['template_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

class SMSProvider(models.Model):
    """SMS provider configuration"""

    PROVIDER_TYPES = (
        ('africastalking', 'Africa\'s Talking'),
        ('twilio', 'Twilio'),
        ('custom', 'Custom Provider'),
    )

    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    api_key = models.CharField(max_length=200)
    api_secret = models.CharField(max_length=200, blank=True, null=True)
    sender_id = models.CharField(max_length=20, help_text="Sender ID for SMS")

    # Configuration
    base_url = models.URLField(blank=True, null=True)
    rate_per_sms = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Status
    is_active = models.BooleanField(default=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'SMS Provider'
        verbose_name_plural = 'SMS Providers'

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"

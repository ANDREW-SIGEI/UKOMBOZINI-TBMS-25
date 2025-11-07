from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'System Administrator'),
        ('field_officer', 'Field Officer'),
        ('group_admin', 'Group Administrator'),
        ('member', 'Group Member'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='field_officer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    id_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    # Field Officer specific fields
    assigned_county = models.CharField(max_length=100, blank=True, null=True)
    assigned_constituency = models.CharField(max_length=100, blank=True, null=True)
    assigned_ward = models.CharField(max_length=100, blank=True, null=True)

    # Status tracking
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    last_location = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} - {self.get_user_type_display()}"

    def get_total_savings(self):
        """Calculate total savings for the user (member)"""
        # Since there's no separate savings model, we'll return a default value
        # In a real implementation, this would calculate from savings transactions
        return Decimal('0.00')

class UserActivity(models.Model):
    ACTION_CHOICES = (
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('create', 'Create Record'),
        ('update', 'Update Record'),
        ('delete', 'Delete Record'),
        ('approve', 'Approve Loan'),
        ('disburse', 'Disburse Funds'),
        ('meeting', 'Schedule Meeting'),
        ('location_update', 'Location Update'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Related object tracking
    content_type = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"

import uuid
from django.db import models
from django.utils import timezone


class SyncableModel(models.Model):
    """
    Abstract base model for offline synchronization capabilities.
    Provides fields and methods needed for sync operations.
    """

    # Sync fields
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this record was synchronized"
    )
    sync_token = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique token for sync conflict resolution"
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag for sync purposes"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when record was soft deleted"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Generate sync token if not exists
        if not self.sync_token:
            self.sync_token = self._generate_sync_token()

        # Update last_sync_at on save
        self.last_sync_at = timezone.now()

        super().save(*args, **kwargs)

    def _generate_sync_token(self):
        """Generate a unique sync token"""
        return f"{self.__class__.__name__.lower()}_{uuid.uuid4().hex[:16]}_{int(timezone.now().timestamp())}"

    def soft_delete(self):
        """Soft delete the record for sync purposes"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore a soft deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    @property
    def is_synced(self):
        """Check if record has been synced"""
        return self.last_sync_at is not None

    @classmethod
    def get_sync_queryset(cls, last_sync_timestamp=None, sync_token=None):
        """
        Get queryset for sync operations.
        Returns records modified after last_sync_timestamp or with newer sync_tokens.
        """
        queryset = cls.objects.filter(is_deleted=False)

        if last_sync_timestamp:
            queryset = queryset.filter(
                models.Q(last_sync_at__gt=last_sync_timestamp) |
                models.Q(last_sync_at__isnull=True)
            )

        if sync_token:
            # Get records with sync tokens newer than the provided one
            queryset = queryset.filter(sync_token__gt=sync_token)

        return queryset.order_by('last_sync_at', 'id')


class SyncConflict(models.Model):
    """
    Model to track sync conflicts that need resolution
    """

    CONFLICT_TYPES = (
        ('server_wins', 'Server Wins'),
        ('client_wins', 'Client Wins'),
        ('manual_merge', 'Manual Merge Required'),
        ('duplicate', 'Duplicate Record'),
    )

    RESOLUTION_STATUS = (
        ('pending', 'Pending Resolution'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    )

    # Conflict details
    model_name = models.CharField(max_length=100, help_text="Model class name")
    record_id = models.PositiveIntegerField(help_text="ID of the conflicting record")
    sync_token = models.CharField(max_length=100, help_text="Sync token of the conflicting record")

    # Conflict data
    server_data = models.JSONField(help_text="Current server state")
    client_data = models.JSONField(help_text="Client state that caused conflict")
    conflict_fields = models.JSONField(help_text="Fields that have conflicts")

    # Resolution
    conflict_type = models.CharField(max_length=20, choices=CONFLICT_TYPES, default='manual_merge')
    resolution_status = models.CharField(max_length=20, choices=RESOLUTION_STATUS, default='pending')
    resolved_data = models.JSONField(null=True, blank=True, help_text="Resolved data after conflict resolution")
    resolved_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='resolved_conflicts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    client_info = models.JSONField(null=True, blank=True, help_text="Client device/browser info")

    class Meta:
        app_label = 'ukombozini.apps.sync'
        verbose_name = 'Sync Conflict'
        verbose_name_plural = 'Sync Conflicts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name', 'record_id']),
            models.Index(fields=['resolution_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.model_name} #{self.record_id} - {self.get_resolution_status_display()}"

    def resolve(self, resolution_type, resolved_data=None, resolved_by=None):
        """Resolve the conflict"""
        self.conflict_type = resolution_type
        self.resolution_status = 'resolved'
        self.resolved_data = resolved_data
        self.resolved_by = resolved_by
        self.resolved_at = timezone.now()
        self.save()

    def ignore(self):
        """Ignore the conflict"""
        self.resolution_status = 'ignored'
        self.save()


class SyncSession(models.Model):
    """
    Track sync sessions for debugging and monitoring
    """

    SESSION_TYPES = (
        ('full_sync', 'Full Synchronization'),
        ('incremental_sync', 'Incremental Synchronization'),
        ('conflict_resolution', 'Conflict Resolution'),
    )

    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    )

    # Session info
    session_id = models.CharField(max_length=100, unique=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='sync_sessions')

    # Sync details
    last_sync_timestamp = models.DateTimeField(null=True, blank=True)
    records_synced = models.PositiveIntegerField(default=0)
    conflicts_found = models.PositiveIntegerField(default=0)
    errors_count = models.PositiveIntegerField(default=0)

    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Client info
    client_info = models.JSONField(null=True, blank=True, help_text="Client device/browser info")
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Error details
    error_message = models.TextField(blank=True, null=True)
    error_details = models.JSONField(null=True, blank=True)

    class Meta:
        app_label = 'ukombozini.apps.sync'
        verbose_name = 'Sync Session'
        verbose_name_plural = 'Sync Sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['session_type']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.session_type} - {self.status}"

    def complete(self, records_synced=0, conflicts_found=0, errors_count=0):
        """Mark session as completed"""
        self.status = 'completed'
        self.records_synced = records_synced
        self.conflicts_found = conflicts_found
        self.errors_count = errors_count
        self.completed_at = timezone.now()
        self.save()

    def fail(self, error_message=None, error_details=None):
        """Mark session as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.error_details = error_details
        self.completed_at = timezone.now()
        self.save()

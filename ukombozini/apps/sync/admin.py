from django.contrib import admin
from .models import SyncSession, SyncConflict


@admin.register(SyncSession)
class SyncSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'session_type', 'user', 'status', 'started_at', 'completed_at', 'records_synced', 'conflicts_found']
    list_filter = ['session_type', 'status', 'started_at']
    search_fields = ['session_id', 'user__username']
    readonly_fields = ['session_id', 'started_at', 'completed_at', 'error_message']


@admin.register(SyncConflict)
class SyncConflictAdmin(admin.ModelAdmin):
    list_display = ['id', 'model_name', 'record_id', 'conflict_type', 'resolution_status', 'created_at']
    list_filter = ['model_name', 'conflict_type', 'resolution_status', 'created_at']
    search_fields = ['model_name', 'record_id']
    readonly_fields = ['id', 'created_at', 'resolved_at']

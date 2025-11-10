from rest_framework import serializers
from .models import SyncSession, SyncConflict


class SyncSessionSerializer(serializers.ModelSerializer):
    """Serializer for sync sessions"""

    class Meta:
        model = SyncSession
        fields = [
            'session_id', 'session_type', 'status', 'started_at', 'completed_at',
            'records_synced', 'conflicts_found', 'errors_count', 'error_message',
            'client_info'
        ]
        read_only_fields = ['session_id', 'started_at', 'completed_at']


class SyncConflictSerializer(serializers.ModelSerializer):
    """Serializer for sync conflicts"""

    class Meta:
        model = SyncConflict
        fields = [
            'id', 'model_name', 'record_id', 'sync_token', 'server_data',
            'client_data', 'conflict_fields', 'conflict_type', 'resolution_status',
            'resolved_data', 'created_at', 'client_info'
        ]
        read_only_fields = ['id', 'created_at']


class SyncPullSerializer(serializers.Serializer):
    """Serializer for sync pull requests"""

    last_sync_timestamp = serializers.DateTimeField(required=False, allow_null=True)
    sync_token = serializers.CharField(required=False, allow_blank=True)
    model_names = serializers.ListField(
        child=serializers.CharField(),
        required=True
    )

    def validate_model_names(self, value):
        """Validate that requested models are sync-enabled"""
        valid_models = [
            'meeting_schedule', 'field_visit', 'event', 'event_attendance',
            'loan', 'loan_repayment', 'savings_transaction', 'message'
        ]

        invalid_models = [model for model in value if model not in valid_models]
        if invalid_models:
            raise serializers.ValidationError(f"Invalid model names: {invalid_models}")

        return value


class SyncPushSerializer(serializers.Serializer):
    """Serializer for sync push requests"""

    changes = serializers.DictField(required=True)
    resolve_conflicts = serializers.BooleanField(default=False)

    def validate_changes(self, value):
        """Validate the structure of changes"""
        valid_models = [
            'meeting_schedule', 'field_visit', 'event', 'event_attendance',
            'loan', 'loan_repayment', 'savings_transaction', 'message'
        ]

        for model_name, changes in value.items():
            if model_name not in valid_models:
                raise serializers.ValidationError(f"Invalid model: {model_name}")

            if not isinstance(changes, list):
                raise serializers.ValidationError(f"Changes for {model_name} must be a list")

            for change in changes:
                if not isinstance(change, dict):
                    raise serializers.ValidationError("Each change must be a dictionary")

                if 'type' not in change:
                    raise serializers.ValidationError("Each change must have a 'type' field")

                if change['type'] not in ['create', 'update', 'delete']:
                    raise serializers.ValidationError("Change type must be 'create', 'update', or 'delete'")

                if change['type'] in ['create', 'update'] and 'data' not in change:
                    raise serializers.ValidationError("Create/update changes must have 'data' field")

                if 'sync_token' not in change:
                    raise serializers.ValidationError("Each change must have a 'sync_token' field")

        return value


class SyncDataSerializer(serializers.Serializer):
    """Serializer for sync data"""

    id = serializers.IntegerField()
    sync_token = serializers.CharField()
    last_sync_at = serializers.DateTimeField(allow_null=True)
    is_deleted = serializers.BooleanField()
    data = serializers.DictField()


class SyncResponseSerializer(serializers.Serializer):
    """Serializer for sync responses"""

    session_id = serializers.CharField()
    changes = serializers.DictField(child=serializers.ListField(child=SyncDataSerializer()))
    conflicts = serializers.ListField(child=SyncConflictSerializer())
    server_timestamp = serializers.DateTimeField()

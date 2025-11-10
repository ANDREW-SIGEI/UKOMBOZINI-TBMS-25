from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
import json

from .models import SyncSession, SyncConflict, SyncableModel
from .serializers import (
    SyncSessionSerializer,
    SyncConflictSerializer,
    SyncPullSerializer,
    SyncPushSerializer
)


class SyncViewSet(viewsets.ViewSet):
    """
    ViewSet for handling offline synchronization operations
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def pull(self, request):
        """
        Pull changes from server since last sync
        """
        serializer = SyncPullSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        last_sync_timestamp = serializer.validated_data.get('last_sync_timestamp')
        sync_token = serializer.validated_data.get('sync_token')
        model_names = serializer.validated_data.get('model_names', [])

        # Create sync session
        sync_session = SyncSession.objects.create(
            session_id=f"sync_{request.user.id}_{int(timezone.now().timestamp())}",
            session_type='incremental_sync',
            user=request.user,
            last_sync_timestamp=last_sync_timestamp
        )

        try:
            with transaction.atomic():
                changes = {}
                conflicts = []

                # Get changes for each model
                for model_name in model_names:
                    try:
                        model_class = self._get_model_class(model_name)
                        queryset = model_class.get_sync_queryset(
                            last_sync_timestamp=last_sync_timestamp,
                            sync_token=sync_token
                        )

                        # Convert to dict format
                        model_changes = []
                        for obj in queryset:
                            model_changes.append({
                                'id': obj.id,
                                'sync_token': obj.sync_token,
                                'last_sync_at': obj.last_sync_at.isoformat() if obj.last_sync_at else None,
                                'is_deleted': obj.is_deleted,
                                'data': self._model_to_dict(obj)
                            })

                        changes[model_name] = model_changes

                    except Exception as e:
                        sync_session.errors_count += 1
                        sync_session.error_details = {
                            **(sync_session.error_details or {}),
                            model_name: str(e)
                        }

                # Check for conflicts (server changes that conflict with client)
                server_conflicts = self._detect_conflicts(request.user, serializer.validated_data)

                sync_session.complete(
                    records_synced=sum(len(changes.get(model, [])) for model in model_names),
                    conflicts_found=len(server_conflicts)
                )

                return Response({
                    'session_id': sync_session.session_id,
                    'changes': changes,
                    'conflicts': server_conflicts,
                    'server_timestamp': timezone.now().isoformat()
                })

        except Exception as e:
            sync_session.fail(str(e))
            return Response(
                {'error': 'Sync failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def push(self, request):
        """
        Push local changes to server
        """
        serializer = SyncPushSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        client_changes = serializer.validated_data.get('changes', {})
        resolve_conflicts = serializer.validated_data.get('resolve_conflicts', False)

        # Create sync session
        sync_session = SyncSession.objects.create(
            session_id=f"sync_{request.user.id}_{int(timezone.now().timestamp())}",
            session_type='incremental_sync',
            user=request.user
        )

        try:
            with transaction.atomic():
                results = {}
                conflicts = []

                # Process each model's changes
                for model_name, changes in client_changes.items():
                    try:
                        model_class = self._get_model_class(model_name)
                        model_results = []

                        for change in changes:
                            result = self._apply_change(
                                model_class,
                                change,
                                request.user,
                                resolve_conflicts
                            )

                            if result.get('conflict'):
                                conflicts.append(result['conflict'])
                            else:
                                model_results.append(result)

                        results[model_name] = model_results

                    except Exception as e:
                        sync_session.errors_count += 1
                        sync_session.error_details = {
                            **(sync_session.error_details or {}),
                            model_name: str(e)
                        }

                sync_session.complete(
                    records_synced=sum(len(results.get(model, [])) for model in client_changes.keys()),
                    conflicts_found=len(conflicts)
                )

                return Response({
                    'session_id': sync_session.session_id,
                    'results': results,
                    'conflicts': conflicts,
                    'server_timestamp': timezone.now().isoformat()
                })

        except Exception as e:
            sync_session.fail(str(e))
            return Response(
                {'error': 'Sync failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def full_sync(self, request):
        """
        Perform full synchronization (get all data)
        """
        model_names = request.data.get('model_names', [])

        sync_session = SyncSession.objects.create(
            session_id=f"full_sync_{request.user.id}_{int(timezone.now().timestamp())}",
            session_type='full_sync',
            user=request.user
        )

        try:
            with transaction.atomic():
                all_data = {}

                for model_name in model_names:
                    try:
                        model_class = self._get_model_class(model_name)
                        queryset = model_class.objects.filter(is_deleted=False)

                        model_data = []
                        for obj in queryset:
                            model_data.append({
                                'id': obj.id,
                                'sync_token': obj.sync_token,
                                'last_sync_at': obj.last_sync_at.isoformat() if obj.last_sync_at else None,
                                'data': self._model_to_dict(obj)
                            })

                        all_data[model_name] = model_data

                    except Exception as e:
                        sync_session.errors_count += 1
                        sync_session.error_details = {
                            **(sync_session.error_details or {}),
                            model_name: str(e)
                        }

                sync_session.complete(records_synced=sum(len(all_data.get(model, [])) for model in model_names))

                return Response({
                    'session_id': sync_session.session_id,
                    'data': all_data,
                    'server_timestamp': timezone.now().isoformat()
                })

        except Exception as e:
            sync_session.fail(str(e))
            return Response(
                {'error': 'Full sync failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_model_class(self, model_name):
        """Get model class from string name"""
        from django.apps import apps

        # Map model names to actual model classes
        model_mapping = {
            'meeting_schedule': 'dashboard.MeetingSchedule',
            'field_visit': 'dashboard.FieldVisit',
            'event': 'dashboard.Event',
            'event_attendance': 'dashboard.EventAttendance',
            'loan': 'loans.Loan',
            'loan_repayment': 'loans.LoanRepayment',
            'savings_transaction': 'savings.SavingsTransaction',
            'message': 'messaging.Message',
        }

        if model_name not in model_mapping:
            raise ValueError(f"Unknown model: {model_name}")

        app_label, model_name = model_mapping[model_name].split('.')
        return apps.get_model(app_label, model_name)

    def _model_to_dict(self, obj):
        """Convert model instance to dictionary"""
        # Get all fields except sync fields
        data = {}
        for field in obj._meta.fields:
            if field.name not in ['last_sync_at', 'sync_token', 'is_deleted', 'deleted_at']:
                value = getattr(obj, field.name)
                if hasattr(value, 'isoformat'):  # DateTime field
                    data[field.name] = value.isoformat()
                else:
                    data[field.name] = value
        return data

    def _apply_change(self, model_class, change, user, resolve_conflicts=False):
        """Apply a single change from client"""
        change_type = change.get('type')  # 'create', 'update', 'delete'
        data = change.get('data', {})
        sync_token = change.get('sync_token')

        try:
            if change_type == 'create':
                # Check for existing record with same sync_token
                existing = model_class.objects.filter(sync_token=sync_token).first()
                if existing:
                    # This might be a conflict or duplicate
                    if resolve_conflicts:
                        # Update existing
                        for key, value in data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        existing.save()
                        return {'id': existing.id, 'action': 'updated'}
                    else:
                        return {'conflict': self._create_conflict(existing, data, user)}

                # Create new record
                obj = model_class(**data)
                obj.save()
                return {'id': obj.id, 'action': 'created'}

            elif change_type == 'update':
                obj = model_class.objects.filter(sync_token=sync_token).first()
                if not obj:
                    # Object doesn't exist on server
                    return {'conflict': self._create_conflict(None, data, user, conflict_type='missing_record')}

                # Check for conflicts
                server_data = self._model_to_dict(obj)
                conflicts = self._find_field_conflicts(server_data, data)

                if conflicts and not resolve_conflicts:
                    return {'conflict': self._create_conflict(obj, data, user, conflicts)}

                # Apply update
                for key, value in data.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
                obj.save()
                return {'id': obj.id, 'action': 'updated'}

            elif change_type == 'delete':
                obj = model_class.objects.filter(sync_token=sync_token).first()
                if obj:
                    obj.soft_delete()
                    return {'id': obj.id, 'action': 'deleted'}
                return {'action': 'not_found'}

        except Exception as e:
            return {'error': str(e)}

    def _detect_conflicts(self, user, sync_data):
        """Detect conflicts between server and client state"""
        # This is a simplified conflict detection
        # In practice, you'd compare sync_tokens and timestamps
        return []

    def _find_field_conflicts(self, server_data, client_data):
        """Find conflicting fields between server and client data"""
        conflicts = []
        for key, client_value in client_data.items():
            server_value = server_data.get(key)
            if client_value != server_value:
                conflicts.append({
                    'field': key,
                    'server_value': server_value,
                    'client_value': client_value
                })
        return conflicts

    def _create_conflict(self, server_obj, client_data, user, conflicts=None, conflict_type='manual_merge'):
        """Create a sync conflict record"""
        conflict = SyncConflict.objects.create(
            model_name=server_obj.__class__.__name__ if server_obj else 'Unknown',
            record_id=server_obj.id if server_obj else None,
            sync_token=server_obj.sync_token if server_obj else None,
            server_data=self._model_to_dict(server_obj) if server_obj else {},
            client_data=client_data,
            conflict_fields=conflicts or [],
            conflict_type=conflict_type,
            client_info={'user_id': user.id, 'user_agent': 'sync_client'}
        )
        return SyncConflictSerializer(conflict).data


class SyncConflictViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sync conflicts
    """
    queryset = SyncConflict.objects.all()
    serializer_class = SyncConflictSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(resolved_by=self.request.user)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a conflict"""
        conflict = self.get_object()
        resolution_type = request.data.get('resolution_type')
        resolved_data = request.data.get('resolved_data')

        if resolution_type not in ['server_wins', 'client_wins', 'manual_merge']:
            return Response(
                {'error': 'Invalid resolution type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        conflict.resolve(resolution_type, resolved_data, request.user)

        # Apply the resolution
        if resolution_type == 'server_wins':
            # Keep server data
            pass
        elif resolution_type == 'client_wins':
            # Update with client data
            model_class = self._get_model_class(conflict.model_name)
            obj = model_class.objects.get(id=conflict.record_id)
            for key, value in conflict.client_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            obj.save()
        elif resolution_type == 'manual_merge' and resolved_data:
            # Apply manually resolved data
            model_class = self._get_model_class(conflict.model_name)
            obj = model_class.objects.get(id=conflict.record_id)
            for key, value in resolved_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            obj.save()

        return Response({'status': 'resolved'})

    def _get_model_class(self, model_name):
        """Get model class from string name"""
        from django.apps import apps

        # Map model names to actual model classes
        model_mapping = {
            'MeetingSchedule': 'dashboard.MeetingSchedule',
            'FieldVisit': 'dashboard.FieldVisit',
            'Event': 'dashboard.Event',
            'EventAttendance': 'dashboard.EventAttendance',
            'Loan': 'loans.Loan',
            'LoanRepayment': 'loans.LoanRepayment',
            'SavingsTransaction': 'savings.SavingsTransaction',
            'Message': 'messaging.Message',
        }

        if model_name not in model_mapping:
            raise ValueError(f"Unknown model: {model_name}")

        app_label, model_name = model_mapping[model_name].split('.')
        return apps.get_model(app_label, model_name)


class SyncSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing sync sessions
    """
    queryset = SyncSession.objects.all()
    serializer_class = SyncSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

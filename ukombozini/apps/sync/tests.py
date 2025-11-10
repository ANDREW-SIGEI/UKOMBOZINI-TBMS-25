from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from .models import SyncSession, SyncConflict, SyncableModel

User = get_user_model()


class SyncableModelTestCase(TestCase):
    """Test cases for SyncableModel base class"""

    def test_sync_token_generation(self):
        """Test that sync tokens are generated automatically"""
        # This would require creating a concrete model that inherits from SyncableModel
        # For now, we'll test the abstract methods exist
        self.assertTrue(hasattr(SyncableModel, 'get_sync_queryset'))
        self.assertTrue(hasattr(SyncableModel, 'soft_delete'))


class SyncSessionTestCase(TestCase):
    """Test cases for SyncSession model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_session_creation(self):
        """Test creating a sync session"""
        session = SyncSession.objects.create(
            session_id='test_session_123',
            session_type='incremental_sync',
            user=self.user
        )

        self.assertEqual(session.session_id, 'test_session_123')
        self.assertEqual(session.session_type, 'incremental_sync')
        self.assertEqual(session.status, 'in_progress')
        self.assertIsNotNone(session.started_at)

    def test_session_completion(self):
        """Test completing a sync session"""
        session = SyncSession.objects.create(
            session_id='test_session_123',
            session_type='incremental_sync',
            user=self.user
        )

        session.complete(records_synced=10, conflicts_found=2)

        self.assertEqual(session.status, 'completed')
        self.assertEqual(session.records_synced, 10)
        self.assertEqual(session.conflicts_found, 2)
        self.assertIsNotNone(session.completed_at)

    def test_session_failure(self):
        """Test failing a sync session"""
        session = SyncSession.objects.create(
            session_id='test_session_123',
            session_type='incremental_sync',
            user=self.user
        )

        session.fail("Test error message")

        self.assertEqual(session.status, 'failed')
        self.assertEqual(session.error_message, "Test error message")
        self.assertIsNotNone(session.completed_at)


class SyncConflictTestCase(TestCase):
    """Test cases for SyncConflict model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_conflict_creation(self):
        """Test creating a sync conflict"""
        conflict = SyncConflict.objects.create(
            model_name='TestModel',
            record_id=1,
            sync_token='test_token_123',
            server_data={'field1': 'server_value'},
            client_data={'field1': 'client_value'},
            conflict_fields=[{'field': 'field1', 'server_value': 'server_value', 'client_value': 'client_value'}],
            conflict_type='manual_merge',
            client_info={'user_id': self.user.id}
        )

        self.assertEqual(conflict.model_name, 'TestModel')
        self.assertEqual(conflict.record_id, 1)
        self.assertEqual(conflict.conflict_type, 'manual_merge')
        self.assertEqual(conflict.resolution_status, 'unresolved')

    def test_conflict_resolution(self):
        """Test resolving a sync conflict"""
        conflict = SyncConflict.objects.create(
            model_name='TestModel',
            record_id=1,
            sync_token='test_token_123',
            server_data={'field1': 'server_value'},
            client_data={'field1': 'client_value'},
            conflict_fields=[],
            conflict_type='manual_merge',
            client_info={'user_id': self.user.id}
        )

        conflict.resolve('client_wins', {'field1': 'client_value'}, self.user)

        self.assertEqual(conflict.resolution_status, 'resolved')
        self.assertEqual(conflict.resolution_type, 'client_wins')
        self.assertEqual(conflict.resolved_data, {'field1': 'client_value'})
        self.assertEqual(conflict.resolved_by, self.user)
        self.assertIsNotNone(conflict.resolved_at)


class SyncAPITestCase(APITestCase):
    """Test cases for sync API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_pull_endpoint(self):
        """Test the sync pull endpoint"""
        url = '/api/sync/pull/'
        data = {
            'model_names': ['meeting_schedule'],
            'last_sync_timestamp': timezone.now().isoformat()
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('changes', response.data)
        self.assertIn('server_timestamp', response.data)

    def test_push_endpoint(self):
        """Test the sync push endpoint"""
        url = '/api/sync/push/'
        data = {
            'changes': {},
            'resolve_conflicts': False
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('results', response.data)
        self.assertIn('server_timestamp', response.data)

    def test_full_sync_endpoint(self):
        """Test the full sync endpoint"""
        url = '/api/sync/full_sync/'
        data = {
            'model_names': ['meeting_schedule']
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('data', response.data)
        self.assertIn('server_timestamp', response.data)

    def test_sync_sessions_endpoint(self):
        """Test listing sync sessions"""
        # Create a test session
        SyncSession.objects.create(
            session_id='test_session_123',
            session_type='incremental_sync',
            user=self.user
        )

        url = '/api/sync/sessions/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

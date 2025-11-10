from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Message, MessageTemplate, SMSProvider
from .services import MessageService

User = get_user_model()

class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            phone_number='+1234567890'
        )

    def test_message_creation(self):
        message = Message.objects.create(
            recipient=self.user,
            message_type='general',
            delivery_method='sms',
            message_body='Test message'
        )
        self.assertEqual(message.status, 'pending')
        self.assertIsNotNone(message.message_id)

class MessageServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            phone_number='+1234567890'
        )
        self.service = MessageService()

    def test_create_message(self):
        message, success, errors = self.service.create_and_send_message(
            recipient=self.user,
            message_type='general',
            delivery_method='sms',
            message_body='Test message'
        )
        self.assertIsInstance(message, Message)
        self.assertEqual(message.recipient, self.user)

class MessageAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            phone_number='+1234567890'
        )
        self.client.force_authenticate(user=self.user)

    def test_send_message(self):
        data = {
            'recipient_ids': [self.user.id],
            'message_type': 'general',
            'delivery_method': 'sms',
            'message_body': 'Test API message'
        }
        response = self.client.post('/api/messaging/messages/send_message/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class MessageTemplateTest(TestCase):
    def test_template_creation(self):
        template = MessageTemplate.objects.create(
            name='Test Template',
            template_type='general',
            message_template='Hello {name}',
            available_variables='name'
        )
        self.assertEqual(template.name, 'Test Template')
        self.assertTrue(template.is_active)

class SMSProviderTest(TestCase):
    def test_provider_creation(self):
        provider = SMSProvider.objects.create(
            name='Test Provider',
            provider_type='africastalking',
            api_key='test_key',
            api_secret='test_secret',
            sender_id='TEST'
        )
        self.assertEqual(provider.name, 'Test Provider')
        self.assertTrue(provider.is_active)

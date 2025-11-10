from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Message, MessageTemplate, SMSProvider
from .serializers import (
    MessageSerializer, MessageTemplateSerializer, SMSProviderSerializer,
    SendMessageSerializer, BulkGroupMessageSerializer
)
from .services import MessageService
from ukombozini.apps.groups.models import Group
from ukombozini.apps.users.models import CustomUser

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Message.objects.all()
        message_type = self.request.query_params.get('message_type', None)
        status_filter = self.request.query_params.get('status', None)
        recipient = self.request.query_params.get('recipient', None)

        if message_type:
            queryset = queryset.filter(message_type=message_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if recipient:
            queryset = queryset.filter(recipient_id=recipient)

        return queryset

    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Send message to individual recipients"""
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message_service = MessageService()
        sent_messages = []
        failed_messages = []

        for recipient_id in serializer.validated_data['recipient_ids']:
            try:
                recipient = CustomUser.objects.get(id=recipient_id)
                message, success, errors = message_service.create_and_send_message(
                    recipient=recipient,
                    message_type=serializer.validated_data['message_type'],
                    delivery_method=serializer.validated_data['delivery_method'],
                    message_body=serializer.validated_data['message_body'],
                    subject=serializer.validated_data.get('subject'),
                    related_group_id=serializer.validated_data.get('related_group_id'),
                    related_loan_id=serializer.validated_data.get('related_loan_id'),
                    related_meeting_id=serializer.validated_data.get('related_meeting_id'),
                    sent_by=request.user
                )

                if success:
                    sent_messages.append(MessageSerializer(message).data)
                else:
                    failed_messages.append({
                        'recipient_id': recipient_id,
                        'errors': errors
                    })

            except CustomUser.DoesNotExist:
                failed_messages.append({
                    'recipient_id': recipient_id,
                    'errors': ['Recipient not found']
                })

        return Response({
            'sent_messages': sent_messages,
            'failed_messages': failed_messages,
            'total_sent': len(sent_messages),
            'total_failed': len(failed_messages)
        })

    @action(detail=False, methods=['post'])
    def send_group_message(self, request):
        """Send message to all members of a group"""
        serializer = BulkGroupMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = Group.objects.get(id=serializer.validated_data['group_id'])
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

        message_service = MessageService()
        sent_messages, failed_messages = message_service.send_group_message(
            group=group,
            message_type=serializer.validated_data['message_type'],
            message_body=serializer.validated_data['message_body'],
            subject=serializer.validated_data.get('subject'),
            delivery_method=serializer.validated_data['delivery_method'],
            sent_by=request.user,
            exclude_members=serializer.validated_data.get('exclude_member_ids', [])
        )

        return Response({
            'group_name': group.name,
            'total_members': group.total_members,
            'sent_messages_count': len(sent_messages),
            'failed_messages_count': len(failed_messages),
            'sent_messages': MessageSerializer(sent_messages, many=True).data,
            'failed_messages': [
                {
                    'recipient': msg.recipient.get_full_name(),
                    'errors': errors
                } for msg, errors in failed_messages
            ]
        })

    @action(detail=True, methods=['post'])
    def retry_send(self, request, pk=None):
        """Retry sending a failed message"""
        message = self.get_object()
        if message.status != 'failed':
            return Response({'error': 'Message is not in failed status'}, status=status.HTTP_400_BAD_REQUEST)

        message_service = MessageService()
        success, errors = message_service.send_message(message)

        if success:
            return Response({'status': 'Message sent successfully'})
        else:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

class MessageTemplateViewSet(viewsets.ModelViewSet):
    queryset = MessageTemplate.objects.all()
    serializer_class = MessageTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MessageTemplate.objects.filter(is_active=True)
        template_type = self.request.query_params.get('template_type', None)
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class SMSProviderViewSet(viewsets.ModelViewSet):
    queryset = SMSProvider.objects.all()
    serializer_class = SMSProviderSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test SMS provider connection"""
        provider = self.get_object()
        # This would implement actual testing logic
        return Response({'status': 'Connection test not implemented yet'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get messaging statistics"""
        from .utils import get_message_stats
        stats = get_message_stats()
        return Response(stats)

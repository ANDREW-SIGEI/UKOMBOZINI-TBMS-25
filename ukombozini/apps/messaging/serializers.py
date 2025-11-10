from rest_framework import serializers
from .models import Message, MessageTemplate, SMSProvider

class MessageSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    sent_by_name = serializers.CharField(source='sent_by.get_full_name', read_only=True)
    related_group_name = serializers.CharField(source='related_group.name', read_only=True)
    related_loan_number = serializers.CharField(source='related_loan.loan_number', read_only=True)
    related_meeting_title = serializers.CharField(source='related_meeting.title', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'message_id', 'message_type', 'delivery_method',
            'recipient', 'recipient_name', 'recipient_phone', 'recipient_email',
            'subject', 'message_body',
            'related_group', 'related_group_name', 'related_loan', 'related_loan_number',
            'related_meeting', 'related_meeting_title',
            'status', 'sent_at', 'delivered_at', 'failed_at',
            'error_message', 'retry_count', 'provider_reference', 'cost',
            'sent_by', 'sent_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'message_id', 'sent_at', 'delivered_at', 'failed_at', 'created_at', 'updated_at']

class MessageTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = MessageTemplate
        fields = [
            'id', 'name', 'template_type', 'subject_template', 'message_template',
            'available_variables', 'is_active', 'is_default',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SMSProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSProvider
        fields = [
            'id', 'name', 'provider_type', 'api_key', 'api_secret', 'sender_id',
            'base_url', 'rate_per_sms', 'is_active', 'balance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'balance', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True}
        }

class SendMessageSerializer(serializers.Serializer):
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of user IDs to send message to"
    )
    message_type = serializers.ChoiceField(
        choices=Message.MESSAGE_TYPES,
        default='general'
    )
    delivery_method = serializers.ChoiceField(
        choices=Message.DELIVERY_METHODS,
        default='sms'
    )
    subject = serializers.CharField(max_length=200, required=False)
    message_body = serializers.CharField(help_text="Message content")
    related_group_id = serializers.IntegerField(required=False)
    related_loan_id = serializers.IntegerField(required=False)
    related_meeting_id = serializers.IntegerField(required=False)

class BulkGroupMessageSerializer(serializers.Serializer):
    group_id = serializers.IntegerField(help_text="Group ID to send message to")
    message_type = serializers.ChoiceField(
        choices=Message.MESSAGE_TYPES,
        default='general'
    )
    delivery_method = serializers.ChoiceField(
        choices=Message.DELIVERY_METHODS,
        default='sms'
    )
    subject = serializers.CharField(max_length=200, required=False)
    message_body = serializers.CharField(help_text="Message content")
    exclude_member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of member IDs to exclude"
    )

from django.contrib import admin
from .models import Message, MessageTemplate, SMSProvider

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'message_id', 'recipient', 'message_type', 'delivery_method',
        'status', 'sent_at', 'created_at'
    ]
    list_filter = ['message_type', 'delivery_method', 'status', 'sent_at', 'created_at']
    search_fields = ['message_id', 'recipient__first_name', 'recipient__last_name', 'recipient__phone_number']
    readonly_fields = ['message_id', 'sent_at', 'delivered_at', 'failed_at', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('message_id', 'message_type', 'delivery_method')
        }),
        ('Recipient', {
            'fields': ('recipient', 'recipient_phone', 'recipient_email')
        }),
        ('Content', {
            'fields': ('subject', 'message_body')
        }),
        ('Related Objects', {
            'fields': ('related_group', 'related_loan', 'related_meeting')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'sent_at', 'delivered_at', 'failed_at', 'error_message', 'retry_count')
        }),
        ('Provider Details', {
            'fields': ('provider_reference', 'cost')
        }),
        ('Audit', {
            'fields': ('sent_by', 'created_at', 'updated_at')
        }),
    )

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'is_default', 'created_at']
    list_filter = ['template_type', 'is_active', 'is_default']
    search_fields = ['name', 'template_type']
    ordering = ['template_type', 'name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template_type', 'is_active', 'is_default')
        }),
        ('Templates', {
            'fields': ('subject_template', 'message_template')
        }),
        ('Configuration', {
            'fields': ('available_variables',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

@admin.register(SMSProvider)
class SMSProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'sender_id', 'is_active', 'balance', 'rate_per_sms']
    list_filter = ['provider_type', 'is_active']
    search_fields = ['name', 'sender_id']
    readonly_fields = ['balance', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider_type', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_secret', 'sender_id', 'base_url')
        }),
        ('Pricing', {
            'fields': ('rate_per_sms', 'balance')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )

from .services import MessageService, MessageTemplateService
from django.utils import timezone
from decimal import Decimal

def send_loan_balance_notification(loan):
    """Send loan balance notification to member"""
    template_service = MessageTemplateService()

    context_data = {
        'member_name': loan.member.get_full_name(),
        'loan_number': loan.loan_number,
        'principal_amount': loan.principal_amount,
        'current_balance': loan.current_balance,
        'total_repayable': loan.total_repayable,
        'due_date': loan.due_date,
        'days_in_arrears': loan.days_in_arrears,
        'arrears_amount': loan.arrears_amount,
        'group_name': loan.group.name,
    }

    message, success, errors = template_service.create_message_from_template(
        template_type='loan_balance',
        context_data=context_data,
        recipient=loan.member,
        delivery_method='sms',
        related_loan=loan,
        related_group=loan.group
    )

    return message, success, errors

def send_meeting_notification(meeting):
    """Send meeting notification to group members"""
    template_service = MessageTemplateService()

    context_data = {
        'member_name': '{{ member_name }}',  # Will be replaced per member
        'group_name': meeting.group.name if meeting.group else 'N/A',
        'meeting_title': meeting.title,
        'meeting_date': meeting.scheduled_date,
        'meeting_time': meeting.scheduled_time,
        'meeting_venue': meeting.venue,
        'meeting_agenda': meeting.description or 'Regular meeting',
    }

    message, success, errors = template_service.create_message_from_template(
        template_type='meeting_notification',
        context_data=context_data,
        recipient=None,  # Will be set per member
        delivery_method='sms',
        related_meeting=meeting,
        related_group=meeting.group
    )

    # Send to all group members
    if meeting.group:
        message_service = MessageService()
        sent_messages, failed_messages = message_service.send_group_message(
            group=meeting.group,
            message_type='meeting_notification',
            message_body=message.message_body if message else f"""UKOMBOZINI Meeting Notification

Group: {meeting.group.name}
Title: {meeting.title}
Date: {meeting.scheduled_date}
Time: {meeting.scheduled_time}
Venue: {meeting.venue}

Please attend this important meeting.

UKOMBOZINI SACCO""",
            subject=f"Meeting Notification: {meeting.title}",
            delivery_method='sms',
            related_meeting=meeting
        )
        return sent_messages, failed_messages

    return [], []

def send_savings_update_notification(member, amount, transaction_type):
    """Send savings update notification to member"""
    template_service = MessageTemplateService()

    context_data = {
        'member_name': member.get_full_name(),
        'amount': amount,
        'transaction_type': transaction_type,
        'group_name': member.group.name,
        'total_savings': member.get_total_savings(),
    }

    message, success, errors = template_service.create_message_from_template(
        template_type='savings_update',
        context_data=context_data,
        recipient=member.user,
        delivery_method='sms',
        related_group=member.group
    )

    return message, success, errors

def send_field_visit_notification(visit):
    """Send field visit notification to group members"""
    template_service = MessageTemplateService()

    context_data = {
        'member_name': '{{ member_name }}',  # Will be replaced per member
        'group_name': visit.group.name,
        'visit_date': visit.scheduled_date,
        'visit_time': visit.scheduled_time,
        'visit_location': visit.location,
        'visit_purpose': visit.purpose or 'Regular field visit',
    }

    message, success, errors = template_service.create_message_from_template(
        template_type='field_visit',
        context_data=context_data,
        recipient=None,  # Will be set per member
        delivery_method='sms',
        related_group=visit.group
    )

    # Send to all group members
    message_service = MessageService()
    sent_messages, failed_messages = message_service.send_group_message(
        group=visit.group,
        message_type='field_visit',
        message_body=message.message_body if message else f"""UKOMBOZINI Field Visit Notification

Group: {visit.group.name}
Date: {visit.scheduled_date}
Time: {visit.scheduled_time}
Location: {visit.location}

Purpose: {visit.purpose or 'Regular field visit'}

Please be available at the location.

UKOMBOZINI SACCO""",
        subject=f"Field Visit Notification: {visit.group.name}",
        delivery_method='sms'
    )

    return sent_messages, failed_messages

def send_bulk_group_notification(group, message_body, subject=None, sent_by=None):
    """Send bulk notification to all group members"""
    message_service = MessageService()

    sent_messages, failed_messages = message_service.send_group_message(
        group=group,
        message_type='general',
        message_body=message_body,
        subject=subject,
        delivery_method='sms',
        sent_by=sent_by
    )

    return sent_messages, failed_messages

def create_default_templates():
    """Create default message templates"""
    from .models import MessageTemplate

    templates_data = [
        {
            'name': 'Loan Balance Update',
            'template_type': 'loan_balance',
            'subject_template': 'Loan Balance Update - {{ loan_number }}',
            'message_template': """Dear {{ member_name }},

Your loan balance update:
Loan Number: {{ loan_number }}
Principal: KES {{ principal_amount }}
Current Balance: KES {{ current_balance }}
Total Repayable: KES {{ total_repayable }}
Due Date: {{ due_date }}

{% if days_in_arrears > 0 %}
ARREARS: {{ days_in_arrears }} days overdue
Arrears Amount: KES {{ arrears_amount }}
{% endif %}

Please make your payments on time.

UKOMBOZINI SACCO""",
            'available_variables': [
                'member_name', 'loan_number', 'principal_amount', 'current_balance',
                'total_repayable', 'due_date', 'days_in_arrears', 'arrears_amount', 'group_name'
            ],
            'is_default': True
        },
        {
            'name': 'Meeting Notification',
            'template_type': 'meeting_notification',
            'subject_template': 'Meeting Notification - {{ meeting_title }}',
            'message_template': """Dear {{ member_name }},

You are invited to the following meeting:

Group: {{ group_name }}
Title: {{ meeting_title }}
Date: {{ meeting_date }}
Time: {{ meeting_time }}
Venue: {{ meeting_venue }}

Agenda: {{ meeting_agenda }}

Please attend this important meeting.

UKOMBOZINI SACCO""",
            'available_variables': [
                'member_name', 'group_name', 'meeting_title', 'meeting_date',
                'meeting_time', 'meeting_venue', 'meeting_agenda'
            ],
            'is_default': True
        },
        {
            'name': 'Savings Update',
            'template_type': 'savings_update',
            'subject_template': 'Savings Update',
            'message_template': """Dear {{ member_name }},

Your savings have been updated:

Transaction: {{ transaction_type }}
Amount: KES {{ amount }}
Total Savings: KES {{ total_savings }}

Thank you for your continued savings.

UKOMBOZINI SACCO""",
            'available_variables': [
                'member_name', 'amount', 'transaction_type', 'total_savings', 'group_name'
            ],
            'is_default': True
        }
    ]

    for template_data in templates_data:
        template, created = MessageTemplate.objects.get_or_create(
            template_type=template_data['template_type'],
            is_default=True,
            defaults=template_data
        )
        if created:
            print(f"Created default template: {template.name}")

def get_message_stats():
    """Get messaging statistics"""
    from .models import Message
    from django.db.models import Count, Sum
    from django.utils import timezone
    import datetime

    # Get stats for last 30 days
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)

    stats = Message.objects.filter(created_at__gte=thirty_days_ago).aggregate(
        total_messages=Count('id'),
        sent_messages=Count('id', filter=models.Q(status='sent')),
        delivered_messages=Count('id', filter=models.Q(status='delivered')),
        failed_messages=Count('id', filter=models.Q(status='failed')),
        total_cost=Sum('cost')
    )

    return stats

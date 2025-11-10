from django.core.management.base import BaseCommand
from ukombozini.apps.messaging.models import MessageTemplate

class Command(BaseCommand):
    help = 'Create default message templates'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Meeting Notification',
                'template_type': 'meeting_notification',
                'subject_template': 'New Meeting Scheduled: {{ meeting_title }}',
                'message_template': '''Dear {{ member_name }},

A new meeting has been scheduled:

Group: {{ group_name }}
Title: {{ meeting_title }}
Date: {{ meeting_date }}
Time: {{ meeting_time }}
Venue: {{ meeting_venue }}

Agenda: {{ meeting_agenda }}

Please attend this important meeting.

UKOMBOZINI SACCO''',
                'available_variables': ['member_name', 'group_name', 'meeting_title', 'meeting_date', 'meeting_time', 'meeting_venue', 'meeting_agenda'],
                'is_default': True
            },
            {
                'name': 'Field Visit Notification',
                'template_type': 'field_visit',
                'subject_template': 'Field Visit Scheduled: {{ group_name }}',
                'message_template': '''Dear {{ member_name }},

A field visit has been scheduled for your group:

Group: {{ group_name }}
Date: {{ visit_date }}
Time: {{ visit_time }}
Location: {{ visit_location }}

Purpose: {{ visit_purpose }}

Please be available at the location.

UKOMBOZINI SACCO''',
                'available_variables': ['member_name', 'group_name', 'visit_date', 'visit_time', 'visit_location', 'visit_purpose'],
                'is_default': True
            },
            {
                'name': 'Loan Balance Update',
                'template_type': 'loan_balance',
                'subject_template': 'Loan Balance Update - {{ loan_number }}',
                'message_template': '''Dear {{ member_name }},

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

UKOMBOZINI SACCO''',
                'available_variables': ['member_name', 'loan_number', 'principal_amount', 'current_balance', 'total_repayable', 'due_date', 'days_in_arrears', 'arrears_amount', 'group_name'],
                'is_default': True
            },
            {
                'name': 'Savings Update',
                'template_type': 'savings_update',
                'subject_template': 'Savings Update',
                'message_template': '''Dear {{ member_name }},

Your savings have been updated:

Transaction: {{ transaction_type }}
Amount: KES {{ amount }}
Total Savings: KES {{ total_savings }}

Thank you for your continued savings.

UKOMBOZINI SACCO''',
                'available_variables': ['member_name', 'amount', 'transaction_type', 'total_savings', 'group_name'],
                'is_default': True
            }
        ]

        for template_data in templates:
            template, created = MessageTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template.name}')
                )

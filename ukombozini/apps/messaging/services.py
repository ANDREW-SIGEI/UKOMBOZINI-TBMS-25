import requests
from django.conf import settings
from django.template import Template, Context
from decimal import Decimal
from .models import Message, MessageTemplate, SMSProvider
import logging

logger = logging.getLogger(__name__)

class SMSService:
    """Service for sending SMS messages"""

    def __init__(self, provider=None):
        self.provider = provider or self.get_default_provider()

    def get_default_provider(self):
        """Get the default active SMS provider"""
        try:
            return SMSProvider.objects.filter(is_active=True).first()
        except:
            return None

    def send_sms(self, phone_number, message, message_obj=None):
        """Send SMS using configured provider"""
        if not self.provider:
            logger.error("No SMS provider configured")
            if message_obj:
                message_obj.mark_as_failed("No SMS provider configured")
            return False, "No SMS provider configured"

        try:
            if self.provider.provider_type == 'africastalking':
                return self._send_africastalking_sms(phone_number, message, message_obj)
            elif self.provider.provider_type == 'twilio':
                return self._send_twilio_sms(phone_number, message, message_obj)
            else:
                logger.error(f"Unsupported provider type: {self.provider.provider_type}")
                if message_obj:
                    message_obj.mark_as_failed(f"Unsupported provider type: {self.provider.provider_type}")
                return False, f"Unsupported provider type: {self.provider.provider_type}"
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            if message_obj:
                message_obj.mark_as_failed(str(e))
            return False, str(e)

    def _send_africastalking_sms(self, phone_number, message, message_obj=None):
        """Send SMS via Africa's Talking"""
        url = "https://api.africastalking.com/version1/messaging"
        headers = {
            'ApiKey': self.provider.api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

        # Ensure phone number starts with +
        if not phone_number.startswith('+'):
            phone_number = f"+{phone_number}"

        data = {
            'username': self.provider.api_key,  # Africa's Talking uses API key as username
            'to': phone_number,
            'message': message,
            'from': self.provider.sender_id
        }

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            result = response.json()
            if result.get('SMSMessageData', {}).get('Recipients'):
                recipient = result['SMSMessageData']['Recipients'][0]
                if recipient.get('status') == 'Success':
                    cost = Decimal(str(recipient.get('cost', 0)))
                    if message_obj:
                        message_obj.mark_as_sent(
                            provider_ref=recipient.get('messageId'),
                            cost=cost
                        )
                    return True, "SMS sent successfully"
                else:
                    error_msg = recipient.get('status', 'Unknown error')
                    if message_obj:
                        message_obj.mark_as_failed(error_msg)
                    return False, error_msg
            else:
                if message_obj:
                    message_obj.mark_as_failed("Invalid response from provider")
                return False, "Invalid response from provider"
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            if message_obj:
                message_obj.mark_as_failed(error_msg)
            return False, error_msg

    def _send_twilio_sms(self, phone_number, message, message_obj=None):
        """Send SMS via Twilio"""
        # This would require twilio-python package
        # For now, return not implemented
        if message_obj:
            message_obj.mark_as_failed("Twilio integration not implemented")
        return False, "Twilio integration not implemented"

class EmailService:
    """Service for sending email messages"""

    def send_email(self, email_address, subject, message_body, message_obj=None):
        """Send email using Django's email backend"""
        from django.core.mail import send_mail

        try:
            sent = send_mail(
                subject=subject,
                message=message_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_address],
                fail_silently=False,
            )

            if sent > 0:
                if message_obj:
                    message_obj.mark_as_sent()
                return True, "Email sent successfully"
            else:
                if message_obj:
                    message_obj.mark_as_failed("Email sending failed")
                return False, "Email sending failed"

        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            if message_obj:
                message_obj.mark_as_failed(str(e))
            return False, str(e)

class MessageService:
    """Main service for handling messages"""

    def __init__(self):
        self.sms_service = SMSService()
        self.email_service = EmailService()

    def send_message(self, message_obj):
        """Send a message based on delivery method"""
        success = False
        errors = []

        if message_obj.delivery_method in ['sms', 'both']:
            sms_success, sms_error = self.sms_service.send_sms(
                message_obj.recipient_phone,
                message_obj.message_body,
                message_obj
            )
            if sms_success:
                success = True
            else:
                errors.append(f"SMS: {sms_error}")

        if message_obj.delivery_method in ['email', 'both']:
            if message_obj.recipient_email:
                email_success, email_error = self.email_service.send_email(
                    message_obj.recipient_email,
                    message_obj.subject or "UKOMBOZINI Message",
                    message_obj.message_body,
                    message_obj
                )
                if email_success:
                    success = True
                else:
                    errors.append(f"Email: {email_error}")
            else:
                errors.append("Email: No email address provided")

        if not success:
            message_obj.mark_as_failed("; ".join(errors))

        return success, errors

    def create_and_send_message(self, recipient, message_type, delivery_method='sms',
                              message_body=None, subject=None, related_group=None,
                              related_loan=None, related_meeting=None, sent_by=None):
        """Create and send a message"""

        # Get recipient contact info
        recipient_phone = getattr(recipient, 'phone_number', None)
        recipient_email = getattr(recipient, 'email', None)

        # Create message object
        message = Message.objects.create(
            message_type=message_type,
            delivery_method=delivery_method,
            recipient=recipient,
            recipient_phone=recipient_phone,
            recipient_email=recipient_email,
            subject=subject,
            message_body=message_body,
            related_group=related_group,
            related_loan=related_loan,
            related_meeting=related_meeting,
            sent_by=sent_by
        )

        # Send the message
        success, errors = self.send_message(message)

        return message, success, errors

    def send_group_message(self, group, message_type, message_body, subject=None,
                          delivery_method='sms', sent_by=None, exclude_members=None):
        """Send message to all members of a group"""
        from ukombozini.apps.members.models import Member

        exclude_ids = exclude_members or []
        members = Member.objects.filter(
            group=group,
            membership_status='active'
        ).exclude(id__in=exclude_ids)

        sent_messages = []
        failed_messages = []

        for member in members:
            message, success, errors = self.create_and_send_message(
                recipient=member.user,
                message_type=message_type,
                delivery_method=delivery_method,
                message_body=message_body,
                subject=subject,
                related_group=group,
                sent_by=sent_by
            )

            if success:
                sent_messages.append(message)
            else:
                failed_messages.append((message, errors))

        return sent_messages, failed_messages

    def send_individual_message(self, recipient, message_type, message_body, subject=None,
                              delivery_method='sms', related_group=None, related_loan=None,
                              related_meeting=None, related_field_visit=None, sent_by=None):
        """Send message to an individual recipient"""
        # Get recipient contact info
        recipient_phone = getattr(recipient, 'phone_number', None)
        recipient_email = getattr(recipient, 'email', None)

        # Create message object
        message = Message.objects.create(
            message_type=message_type,
            delivery_method=delivery_method,
            recipient=recipient,
            recipient_phone=recipient_phone,
            recipient_email=recipient_email,
            subject=subject,
            message_body=message_body,
            related_group=related_group,
            related_loan=related_loan,
            related_meeting=related_meeting,
            related_field_visit=related_field_visit,
            sent_by=sent_by
        )

        # Send the message
        success, errors = self.send_message(message)

        return message, success, errors

class MessageTemplateService:
    """Service for handling message templates"""

    def render_template(self, template, context_data):
        """Render a message template with context data"""
        try:
            subject_template = Template(template.subject_template or "")
            message_template = Template(template.message_template)

            context = Context(context_data)

            rendered_subject = subject_template.render(context) if template.subject_template else ""
            rendered_message = message_template.render(context)

            return rendered_subject, rendered_message
        except Exception as e:
            logger.error(f"Template rendering failed: {str(e)}")
            return "", f"Template rendering failed: {str(e)}"

    def get_template_by_type(self, template_type, is_default=True):
        """Get template by type"""
        try:
            if is_default:
                return MessageTemplate.objects.filter(
                    template_type=template_type,
                    is_active=True,
                    is_default=True
                ).first()
            else:
                return MessageTemplate.objects.filter(
                    template_type=template_type,
                    is_active=True
                ).first()
        except:
            return None

    def create_message_from_template(self, template_type, context_data,
                                   recipient, delivery_method='sms', sent_by=None,
                                   related_group=None, related_loan=None, related_meeting=None):
        """Create message from template"""

        template = self.get_template_by_type(template_type)
        if not template:
            return None, False, ["Template not found"]

        subject, message_body = self.render_template(template, context_data)

        message_service = MessageService()
        return message_service.create_and_send_message(
            recipient=recipient,
            message_type=template_type,
            delivery_method=delivery_method,
            message_body=message_body,
            subject=subject,
            related_group=related_group,
            related_loan=related_loan,
            related_meeting=related_meeting,
            sent_by=sent_by
        )

from django.db.models.signals import post_save
from django.dispatch import receiver
from ukombozini.apps.dashboard.models import MeetingSchedule
from ukombozini.apps.loans.models import LoanRepayment
from ukombozini.apps.members.models import MemberSavings
from .utils import send_meeting_notification, send_loan_balance_notification, send_savings_update_notification

@receiver(post_save, sender=MeetingSchedule)
def send_meeting_notification_on_save(sender, instance, created, **kwargs):
    """Send meeting notification when meeting is created"""
    if created and instance.send_reminder:
        # Send notification to group members
        send_meeting_notification(instance)

@receiver(post_save, sender=LoanRepayment)
def send_loan_balance_notification_on_repayment(sender, instance, created, **kwargs):
    """Send loan balance notification after repayment"""
    if created and instance.is_verified:
        # Send balance update to member
        send_loan_balance_notification(instance.loan)

@receiver(post_save, sender=MemberSavings)
def send_savings_notification_on_transaction(sender, instance, created, **kwargs):
    """Send savings update notification after transaction"""
    if created and instance.is_verified:
        # Send savings update to member
        from ukombozini.apps.members.models import Member
        try:
            member = Member.objects.get(user=instance.member)
            send_savings_update_notification(member, instance.amount, instance.get_savings_type_display())
        except Member.DoesNotExist:
            pass  # Skip if member profile doesn't exist

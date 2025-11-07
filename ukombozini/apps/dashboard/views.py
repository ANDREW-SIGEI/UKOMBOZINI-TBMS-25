from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import MeetingSchedule, FieldVisit, OfficerPerformance, DashboardWidget, OfficerAlert
from .serializers import (
    MeetingScheduleSerializer, FieldVisitSerializer, OfficerPerformanceSerializer,
    DashboardWidgetSerializer, OfficerAlertSerializer, DashboardOverviewSerializer,
    CalendarEventSerializer
)
from ukombozini.apps.groups.models import Group
from ukombozini.apps.loans.models import Loan, LoanRepayment
from ukombozini.apps.members.models import Member
from ukombozini.apps.transactions.models import CashInTransaction, CashOutTransaction

class OfficerDashboardView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get comprehensive dashboard overview for officer"""
        officer = request.user

        # Only field officers and admins can access dashboard
        if officer.user_type not in ['admin', 'field_officer']:
            return Response(
                {'error': 'Only officers can access the dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Calculate date ranges
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        month_start = today.replace(day=1)

        # Base querysets filtered by officer
        if officer.user_type == 'admin':
            meetings_qs = MeetingSchedule.objects.all()
            visits_qs = FieldVisit.objects.all()
            groups_qs = Group.objects.all()
            loans_qs = Loan.objects.all()
            savings_qs = CashInTransaction.objects.filter(transaction_type='savings', status='verified')
        else:
            meetings_qs = MeetingSchedule.objects.filter(officer=officer)
            visits_qs = FieldVisit.objects.filter(officer=officer)
            groups_qs = Group.objects.filter(Q(field_officer=officer) | Q(created_by=officer))
            groups_ids = groups_qs.values_list('id', flat=True)
            loans_qs = Loan.objects.filter(group_id__in=groups_ids)
            savings_qs = CashInTransaction.objects.filter(
                group_id__in=groups_ids,
                transaction_type='savings',
                status='verified'
            )

        # Meeting Statistics
        total_meetings = meetings_qs.count()
        meetings_today = meetings_qs.filter(scheduled_date=today).count()
        meetings_this_week = meetings_qs.filter(
            scheduled_date__range=[week_start, week_end]
        ).count()
        upcoming_meetings = meetings_qs.filter(
            scheduled_date__gte=today,
            status='scheduled'
        ).count()

        # Field Visit Statistics
        total_visits = visits_qs.count()
        visits_this_week = visits_qs.filter(
            scheduled_date__range=[week_start, week_end]
        ).count()
        overdue_visits = visits_qs.filter(
            status='scheduled',
            scheduled_date__lt=today
        ).count()
        visits_completed = visits_qs.filter(status='completed').count()
        visits_completion_rate = (visits_completed / total_visits * 100) if total_visits > 0 else 0

        # Group Statistics
        total_groups = groups_qs.count()
        groups_visited_this_month = visits_qs.filter(
            scheduled_date__gte=month_start,
            status='completed'
        ).values('group').distinct().count()
        groups_visit_rate = (groups_visited_this_month / total_groups * 100) if total_groups > 0 else 0

        # Financial Statistics
        total_savings = savings_qs.aggregate(total=Sum('amount'))['total'] or 0
        total_loans = loans_qs.aggregate(total=Sum('principal_amount'))['total'] or 0
        total_repayments = LoanRepayment.objects.filter(
            loan__in=loans_qs,
            is_verified=True
        ).aggregate(total=Sum('amount_paid'))['total'] or 0

        # Loan Recovery Rate
        total_repayable = loans_qs.aggregate(total=Sum('total_repayable'))['total'] or 0
        loan_recovery_rate = (total_repayments / total_repayable * 100) if total_repayable > 0 else 0

        # Performance Statistics (simplified calculation)
        performance_score = min(100, (
            (meetings_completion_rate * 0.3) +
            (visits_completion_rate * 0.3) +
            (loan_recovery_rate * 0.2) +
            (groups_visit_rate * 0.2)
        ))

        productivity_score = min(100, (
            (total_meetings / max(1, total_groups) * 10) +
            (total_visits / max(1, total_groups) * 10) +
            (loan_recovery_rate * 0.8)
        ))

        efficiency_score = min(100, (
            (meetings_completion_rate * 0.4) +
            (visits_completion_rate * 0.4) +
            (groups_visit_rate * 0.2)
        ))

        # Alert Statistics
        active_alerts = OfficerAlert.objects.filter(
            officer=officer,
            is_dismissed=False
        ).count()

        high_priority_alerts = OfficerAlert.objects.filter(
            officer=officer,
            alert_level__in=['high', 'critical'],
            is_dismissed=False
        ).count()

        overview_data = {
            'total_meetings': total_meetings,
            'meetings_today': meetings_today,
            'meetings_this_week': meetings_this_week,
            'upcoming_meetings': upcoming_meetings,
            'total_visits': total_visits,
            'visits_this_week': visits_this_week,
            'overdue_visits': overdue_visits,
            'visits_completion_rate': visits_completion_rate,
            'total_groups': total_groups,
            'groups_visited_this_month': groups_visited_this_month,
            'groups_visit_rate': groups_visit_rate,
            'total_savings': total_savings,
            'total_loans': total_loans,
            'total_repayments': total_repayments,
            'loan_recovery_rate': loan_recovery_rate,
            'performance_score': performance_score,
            'productivity_score': productivity_score,
            'efficiency_score': efficiency_score,
            'active_alerts': active_alerts,
            'high_priority_alerts': high_priority_alerts,
        }

        serializer = DashboardOverviewSerializer(overview_data)
        return Response(serializer.data)

class MeetingScheduleView(generics.ListCreateAPIView):
    serializer_class = MeetingScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        officer = self.request.user

        if officer.user_type == 'admin':
            return MeetingSchedule.objects.all()
        elif officer.user_type == 'field_officer':
            return MeetingSchedule.objects.filter(officer=officer)
        else:
            return MeetingSchedule.objects.none()

    def perform_create(self, serializer):
        meeting = serializer.save(created_by=self.request.user)

        # Create alert for the meeting
        OfficerAlert.objects.create(
            officer=meeting.officer,
            alert_type='meeting_reminder',
            alert_level='medium',
            title=f'New Meeting Scheduled: {meeting.title}',
            message=f'You have a new meeting scheduled for {meeting.scheduled_date} at {meeting.venue}',
            related_object_type='meeting',
            related_object_id=meeting.id
        )

class FieldVisitView(generics.ListCreateAPIView):
    serializer_class = FieldVisitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        officer = self.request.user

        if officer.user_type == 'admin':
            return FieldVisit.objects.all()
        elif officer.user_type == 'field_officer':
            return FieldVisit.objects.filter(officer=officer)
        else:
            return FieldVisit.objects.none()

    def perform_create(self, serializer):
        visit = serializer.save()

        # Create alert for the visit
        OfficerAlert.objects.create(
            officer=visit.officer,
            alert_type='visit_reminder',
            alert_level='medium',
            title=f'New Field Visit Scheduled: {visit.group.name}',
            message=f'You have a field visit scheduled for {visit.scheduled_date} at {visit.location}',
            related_object_type='field_visit',
            related_object_id=visit.id
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def calendar_events(request):
    """Get calendar events for the officer"""
    officer = request.user
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    events = []

    # Get meetings
    if officer.user_type == 'admin':
        meetings = MeetingSchedule.objects.all()
    else:
        meetings = MeetingSchedule.objects.filter(officer=officer)

    if start_date and end_date:
        meetings = meetings.filter(scheduled_date__range=[start_date, end_date])

    for meeting in meetings:
        events.append({
            'id': meeting.id,
            'title': meeting.title,
            'start': f"{meeting.scheduled_date}T{meeting.scheduled_time}",
            'end': f"{meeting.scheduled_date}T{(meeting.scheduled_time.hour + meeting.expected_duration // 60) % 24}:{(meeting.scheduled_time.minute + meeting.expected_duration % 60) % 60}",
            'type': 'meeting',
            'color': '#3498db',
            'description': meeting.description,
            'location': meeting.venue,
            'status': meeting.status,
        })

    # Get field visits
    if officer.user_type == 'admin':
        visits = FieldVisit.objects.all()
    else:
        visits = FieldVisit.objects.filter(officer=officer)

    if start_date and end_date:
        visits = visits.filter(scheduled_date__range=[start_date, end_date])

    for visit in visits:
        events.append({
            'id': visit.id,
            'title': f"Field Visit: {visit.group.name}",
            'start': f"{visit.scheduled_date}T{visit.scheduled_time}",
            'end': f"{visit.scheduled_date}T{(visit.scheduled_time.hour + 2) % 24}:{visit.scheduled_time.minute}",
            'type': 'visit',
            'color': '#2ecc71',
            'description': visit.purpose,
            'location': visit.location,
            'status': visit.status,
        })

    serializer = CalendarEventSerializer(events, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def loan_overview(request):
    """Get loan overview for officer's groups"""
    officer = request.user

    if officer.user_type == 'admin':
        loans = Loan.objects.all()
    elif officer.user_type == 'field_officer':
        groups = Group.objects.filter(Q(field_officer=officer) | Q(created_by=officer))
        loans = Loan.objects.filter(group__in=groups)
    else:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    # Loan statistics
    total_loans = loans.count()
    total_principal = loans.aggregate(total=Sum('principal_amount'))['total'] or 0
    total_repayable = loans.aggregate(total=Sum('total_repayable'))['total'] or 0
    total_paid = loans.aggregate(total=Sum('total_paid'))['total'] or 0
    current_balance = loans.aggregate(total=Sum('current_balance'))['total'] or 0

    # Loan status breakdown
    status_breakdown = loans.values('status').annotate(
        count=Count('id'),
        amount=Sum('principal_amount')
    )

    # Arrears calculation
    loans_in_arrears = loans.filter(days_in_arrears__gt=0)
    total_arrears = loans_in_arrears.aggregate(total=Sum('arrears_amount'))['total'] or 0
    loans_in_arrears_count = loans_in_arrears.count()

    overview = {
        'total_loans': total_loans,
        'total_principal': total_principal,
        'total_repayable': total_repayable,
        'total_paid': total_paid,
        'current_balance': current_balance,
        'recovery_rate': (total_paid / total_repayable * 100) if total_repayable > 0 else 0,
        'status_breakdown': list(status_breakdown),
        'loans_in_arrears_count': loans_in_arrears_count,
        'total_arrears_amount': total_arrears,
    }

    return Response(overview)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def savings_overview(request):
    """Get savings overview for officer's groups"""
    officer = request.user

    if officer.user_type == 'admin':
        groups = Group.objects.all()
        savings_transactions = CashInTransaction.objects.filter(
            transaction_type='savings',
            status='verified'
        )
    elif officer.user_type == 'field_officer':
        groups = Group.objects.filter(Q(field_officer=officer) | Q(created_by=officer))
        savings_transactions = CashInTransaction.objects.filter(
            group__in=groups,
            transaction_type='savings',
            status='verified'
        )
    else:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    # Total savings
    total_savings = savings_transactions.aggregate(total=Sum('amount'))['total'] or 0

    # Monthly savings trend (last 6 months)
    six_months_ago = date.today() - timedelta(days=180)
    monthly_savings = savings_transactions.filter(
        transaction_date__gte=six_months_ago
    ).extra({
        'month': "EXTRACT(month FROM transaction_date)",
        'year': "EXTRACT(year FROM transaction_date)"
    }).values('year', 'month').annotate(
        total=Sum('amount')
    ).order_by('year', 'month')

    # Group-wise savings
    group_savings = groups.annotate(
        total_savings=Sum('cash_in_transactions__amount', filter=Q(
            cash_in_transactions__transaction_type='savings',
            cash_in_transactions__status='verified'
        ))
    ).values('id', 'name', 'total_savings').order_by('-total_savings')

    # Member savings statistics
    total_members = Member.objects.filter(group__in=groups, membership_status='active').count()
    members_with_savings = Member.objects.filter(
        group__in=groups,
        membership_status='active',
        total_savings__gt=0
    ).count()

    savings_per_member = total_savings / total_members if total_members > 0 else 0

    overview = {
        'total_savings': total_savings,
        'total_groups': groups.count(),
        'total_members': total_members,
        'members_with_savings': members_with_savings,
        'savings_per_member': savings_per_member,
        'monthly_trend': list(monthly_savings),
        'group_breakdown': list(group_savings),
    }

    return Response(overview)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def performance_metrics(request):
    """Get performance metrics for officer"""
    officer = request.user

    if officer.user_type not in ['admin', 'field_officer']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    # Get or create current month performance record
    today = date.today()
    performance, created = OfficerPerformance.objects.get_or_create(
        officer=officer,
        performance_date=today.replace(day=1),
        period_type='monthly',
        defaults={
            'meetings_target': 20,
            'visits_target': 15,
            'savings_target': Decimal('500000.00'),
            'loans_target': Decimal('1000000.00'),
        }
    )

    # Update performance metrics (simplified calculation)
    if officer.user_type == 'admin':
        performance.meetings_scheduled = MeetingSchedule.objects.count()
        performance.meetings_completed = MeetingSchedule.objects.filter(status='completed').count()
        performance.visits_scheduled = FieldVisit.objects.count()
        performance.visits_completed = FieldVisit.objects.filter(status='completed').count()
        performance.groups_assigned = Group.objects.count()
    else:
        performance.meetings_scheduled = MeetingSchedule.objects.filter(officer=officer).count()
        performance.meetings_completed = MeetingSchedule.objects.filter(officer=officer, status='completed').count()
        performance.visits_scheduled = FieldVisit.objects.filter(officer=officer).count()
        performance.visits_completed = FieldVisit.objects.filter(officer=officer, status='completed').count()
        performance.groups_assigned = Group.objects.filter(Q(field_officer=officer) | Q(created_by=officer)).count()

    performance.groups_visited = FieldVisit.objects.filter(
        officer=officer,
        status='completed',
        scheduled_date__gte=today.replace(day=1)
    ).values('group').distinct().count()

    performance.save()

    serializer = OfficerPerformanceSerializer(performance)
    return Response(serializer.data)

class OfficerAlertView(generics.ListAPIView):
    serializer_class = OfficerAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OfficerAlert.objects.filter(
            officer=self.request.user,
            is_dismissed=False
        ).order_by('-alert_date')

    @api_view(['POST'])
    def mark_alert_read(request, alert_id):
        """Mark an alert as read"""
        try:
            alert = OfficerAlert.objects.get(id=alert_id, officer=request.user)
            alert.mark_as_read()
            return Response({'message': 'Alert marked as read'})
        except OfficerAlert.DoesNotExist:
            return Response({'error': 'Alert not found'}, status=status.HTTP_404_NOT_FOUND)

    @api_view(['POST'])
    def dismiss_alert(request, alert_id):
        """Dismiss an alert"""
        try:
            alert = OfficerAlert.objects.get(id=alert_id, officer=request.user)
            alert.dismiss()
            return Response({'message': 'Alert dismissed'})
        except OfficerAlert.DoesNotExist:
            return Response({'error': 'Alert not found'}, status=status.HTTP_404_NOT_FOUND)

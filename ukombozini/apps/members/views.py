from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import Member, NextOfKin, MemberDocument, MemberSavings, MemberActivity, CreditScoreHistory
from .serializers import (
    MemberSerializer, MemberCreateSerializer, MemberUpdateSerializer,
    NextOfKinSerializer, MemberDocumentSerializer, MemberSavingsSerializer,
    MemberActivitySerializer, CreditScoreHistorySerializer,
    MemberFinancialSerializer, MemberCreditScoreSerializer, MemberVerificationSerializer
)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return MemberCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MemberUpdateSerializer
        return MemberSerializer

    def get_queryset(self):
        queryset = Member.objects.select_related('user', 'group', 'created_by')

        # Filter by user permissions
        user = self.request.user
        if user.user_type == 'field_officer':
            # Field officers can only see members in their assigned areas
            queryset = queryset.filter(
                Q(group__county=user.assigned_county) |
                Q(group__constituency=user.assigned_constituency) |
                Q(group__ward=user.assigned_ward)
            )
        elif user.user_type == 'group_admin':
            # Group admins can only see members in their groups
            queryset = queryset.filter(group__created_by=user)

        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(id_number__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(member_number__icontains=search)
            )

        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(membership_status=status_filter)

        # Filter by group
        group_id = self.request.query_params.get('group', None)
        if group_id:
            queryset = queryset.filter(group_id=group_id)

        return queryset

    @action(detail=True, methods=['post'])
    def record_savings(self, request, pk=None):
        """Record a savings transaction for a member"""
        member = self.get_object()
        serializer = MemberFinancialSerializer(data=request.data)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            transaction_type = serializer.validated_data['transaction_type']
            payment_method = serializer.validated_data['payment_method']
            description = serializer.validated_data.get('description', '')
            receipt_number = serializer.validated_data.get('receipt_number', '')

            # Create savings transaction
            savings = MemberSavings.objects.create(
                member=member,
                amount=amount,
                savings_type=transaction_type,
                payment_method=payment_method,
                description=description,
                receipt_number=receipt_number,
                created_by=request.user
            )

            # Log activity
            MemberActivity.objects.create(
                member=member,
                activity_type='savings_deposit',
                description=f"Savings deposit: KES {amount}",
                related_savings=savings,
                performed_by=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            return Response({
                'message': 'Savings recorded successfully',
                'savings_id': savings.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def calculate_credit_score(self, request, pk=None):
        """Recalculate credit score for a member"""
        member = self.get_object()
        serializer = MemberCreditScoreSerializer(data=request.data)

        if serializer.is_valid():
            # Calculate new credit score
            old_score = member.credit_score
            new_score = member.calculate_credit_score()

            # Record in history
            CreditScoreHistory.objects.create(
                member=member,
                credit_score=new_score,
                risk_category=member.risk_category,
                savings_consistency=member.savings_consistency,
                loan_repayment_rate=member.loan_repayment_rate,
                membership_duration_months=member.member_since_months,
                total_fines=member.total_fines_charges,
                score_change=new_score - old_score,
                change_reason=serializer.validated_data.get('notes', 'Manual recalculation')
            )

            # Log activity
            MemberActivity.objects.create(
                member=member,
                activity_type='other',
                description=f"Credit score recalculated: {old_score} -> {new_score}",
                performed_by=request.user
            )

            return Response({
                'message': 'Credit score recalculated',
                'old_score': old_score,
                'new_score': new_score,
                'risk_category': member.risk_category
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def verify_member(self, request, pk=None):
        """Verify member documents or biometric data"""
        member = self.get_object()
        serializer = MemberVerificationSerializer(data=request.data)

        if serializer.is_valid():
            verification_type = serializer.validated_data['verification_type']
            verified = serializer.validated_data['verified']
            notes = serializer.validated_data.get('notes', '')

            # Update verification status
            if verification_type == 'id':
                member.id_verified = verified
                member.id_verification_date = timezone.now() if verified else None
            elif verification_type == 'biometric':
                member.biometric_verified = verified

            member.save()

            # Log activity
            MemberActivity.objects.create(
                member=member,
                activity_type='other',
                description=f"{verification_type.title()} verification: {'Verified' if verified else 'Unverified'}",
                performed_by=request.user
            )

            return Response({
                'message': f'Member {verification_type} verification updated',
                'verified': verified
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get member statistics"""
        queryset = self.get_queryset()

        stats = queryset.aggregate(
            total_members=Count('id'),
            active_members=Count('id', filter=Q(membership_status='active')),
            total_savings=Sum('total_savings'),
            total_loans_taken=Sum('total_loans_taken'),
            average_credit_score=Avg('credit_score')
        )

        # Risk category breakdown
        risk_breakdown = queryset.values('risk_category').annotate(
            count=Count('id')
        ).order_by('risk_category')

        return Response({
            'total_members': stats['total_members'] or 0,
            'active_members': stats['active_members'] or 0,
            'total_savings': stats['total_savings'] or 0,
            'total_loans_taken': stats['total_loans_taken'] or 0,
            'average_credit_score': stats['average_credit_score'] or 0,
            'risk_breakdown': list(risk_breakdown)
        })

class NextOfKinViewSet(viewsets.ModelViewSet):
    queryset = NextOfKin.objects.all()
    serializer_class = NextOfKinSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = NextOfKin.objects.select_related('member')

        # Filter by member if specified
        member_id = self.request.query_params.get('member', None)
        if member_id:
            queryset = queryset.filter(member_id=member_id)

        return queryset

class MemberDocumentViewSet(viewsets.ModelViewSet):
    queryset = MemberDocument.objects.all()
    serializer_class = MemberDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MemberDocument.objects.select_related('member', 'verified_by')

        # Filter by member if specified
        member_id = self.request.query_params.get('member', None)
        if member_id:
            queryset = queryset.filter(member_id=member_id)

        return queryset

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a document"""
        document = self.get_object()
        verified = request.data.get('verified', False)
        notes = request.data.get('notes', '')

        document.is_verified = verified
        document.verified_by = request.user if verified else None
        document.verified_date = timezone.now() if verified else None
        document.save()

        # Log activity
        MemberActivity.objects.create(
            member=document.member,
            activity_type='document_upload',
            description=f"Document '{document.document_name}' {'verified' if verified else 'unverified'}",
            performed_by=request.user
        )

        return Response({'message': 'Document verification updated'})

class MemberSavingsViewSet(viewsets.ModelViewSet):
    queryset = MemberSavings.objects.all()
    serializer_class = MemberSavingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MemberSavings.objects.select_related('member', 'created_by', 'verified_by')

        # Filter by member if specified
        member_id = self.request.query_params.get('member', None)
        if member_id:
            queryset = queryset.filter(member_id=member_id)

        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)

        return queryset

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a savings transaction"""
        savings = self.get_object()
        verified = request.data.get('verified', False)

        savings.is_verified = verified
        savings.verified_by = request.user if verified else None
        savings.save()

        # Update member totals if verified
        if verified:
            savings.update_member_savings()

        return Response({'message': 'Savings transaction verification updated'})

class MemberActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MemberActivity.objects.all()
    serializer_class = MemberActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MemberActivity.objects.select_related('member', 'performed_by', 'related_loan', 'related_savings')

        # Filter by member if specified
        member_id = self.request.query_params.get('member', None)
        if member_id:
            queryset = queryset.filter(member_id=member_id)

        # Filter by activity type
        activity_type = self.request.query_params.get('type', None)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)

        return queryset

class CreditScoreHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CreditScoreHistory.objects.all()
    serializer_class = CreditScoreHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CreditScoreHistory.objects.select_related('member')

        # Filter by member if specified
        member_id = self.request.query_params.get('member', None)
        if member_id:
            queryset = queryset.filter(member_id=member_id)

        return queryset

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def member_dashboard(request):
    """Get dashboard statistics for members"""
    user = request.user

    # Base queryset
    members = Member.objects.all()

    # Apply user permissions
    if user.user_type == 'field_officer':
        members = members.filter(
            Q(group__county=user.assigned_county) |
            Q(group__constituency=user.assigned_constituency) |
            Q(group__ward=user.assigned_ward)
        )
    elif user.user_type == 'group_admin':
        members = members.filter(group__created_by=user)

    # Calculate statistics
    total_members = members.count()
    active_members = members.filter(membership_status='active').count()
    new_members_this_month = members.filter(date_joined__month=date.today().month).count()

    # Financial statistics
    financial_stats = members.aggregate(
        total_savings=Sum('total_savings'),
        total_loans=Sum('total_loans_taken'),
        average_credit_score=Avg('credit_score')
    )

    # Recent activities
    recent_activities = MemberActivity.objects.select_related('member').order_by('-activity_date')[:10]

    # Risk distribution
    risk_distribution = members.values('risk_category').annotate(
        count=Count('id')
    ).order_by('risk_category')

    return Response({
        'total_members': total_members,
        'active_members': active_members,
        'new_members_this_month': new_members_this_month,
        'total_savings': financial_stats['total_savings'] or 0,
        'total_loans': financial_stats['total_loans'] or 0,
        'average_credit_score': financial_stats['average_credit_score'] or 0,
        'risk_distribution': list(risk_distribution),
        'recent_activities': MemberActivitySerializer(recent_activities, many=True).data
    })

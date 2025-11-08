from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from ukombozini.apps.groups.models import Group
from .models import DividendPeriod, MemberDividend, Dividend
from .serializers import (
    DividendPeriodSerializer, MemberDividendSerializer,
    DividendCalculationSerializer, DividendSerializer
)

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit dividend periods
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class DividendPeriodViewSet(viewsets.ModelViewSet):
    queryset = DividendPeriod.objects.all()
    serializer_class = DividendPeriodSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """
        Field officers can only see periods marked as visible
        Admin can see all periods
        """
        queryset = DividendPeriod.objects.all()

        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                # Admin can see all periods
                return queryset
            else:
                # Field officers can only see visible periods
                return queryset.filter(visible_to_field_officers=True)
        return DividendPeriod.objects.none()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def calculate_group_dividends(self, request, pk=None):
        period = self.get_object()
        group_id = request.data.get('group_id')

        if not group_id:
            return Response({
                'status': 'error',
                'message': 'group_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if it's December
        if not period.can_calculate_dividends():
            return Response({
                'status': 'error',
                'message': 'Dividend calculation is only allowed in December for draft periods'
            }, status=status.HTTP_400_BAD_REQUEST)

        success, message = period.calculate_dividends_for_group(group)

        if success:
            report = period.generate_group_dividends_report(group)
            return Response({
                'status': 'success',
                'message': message,
                'report': report
            })
        else:
            return Response({
                'status': 'error',
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def toggle_field_officer_visibility(self, request, pk=None):
        period = self.get_object()
        period.visible_to_field_officers = not period.visible_to_field_officers
        period.save()

        return Response({
            'status': 'success',
            'message': f'Visibility to field officers: {period.visible_to_field_officers}',
            'visible_to_field_officers': period.visible_to_field_officers
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def toggle_member_visibility(self, request, pk=None):
        period = self.get_object()
        period.visible_to_members = not period.visible_to_members
        period.save()

        return Response({
            'status': 'success',
            'message': f'Visibility to members: {period.visible_to_members}',
            'visible_to_members': period.visible_to_members
        })

class MemberDividendViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MemberDividend.objects.all()
    serializer_class = MemberDividendSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Members can only see their own visible dividends
        Field officers can see all visible dividends for their groups
        Admin can see all dividends
        """
        queryset = MemberDividend.objects.all()

        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                # Admin can see all dividends
                return queryset

            elif hasattr(self.request.user, 'member'):
                # Members can only see their own visible dividends
                return queryset.filter(
                    member=self.request.user.member,
                    dividend_period__visible_to_members=True
                )

            elif hasattr(self.request.user, 'officer'):
                # Field officers can see visible dividends for their groups
                officer_groups = self.request.user.officer.groups_assigned.all()
                return queryset.filter(
                    member__group__in=officer_groups,
                    dividend_period__visible_to_field_officers=True
                )

        return MemberDividend.objects.none()

    @action(detail=False, methods=['get'])
    def my_dividends(self, request):
        """Get dividends for the current user (member or field officer)"""
        if hasattr(request.user, 'member'):
            dividends = MemberDividend.objects.filter(
                member=request.user.member,
                dividend_period__visible_to_members=True
            )
            serializer = self.get_serializer(dividends, many=True)
            return Response(serializer.data)

        elif hasattr(request.user, 'officer'):
            # Field officer sees dividends for their groups
            officer_groups = request.user.officer.groups_assigned.all()
            dividends = MemberDividend.objects.filter(
                member__group__in=officer_groups,
                dividend_period__visible_to_field_officers=True
            )
            serializer = self.get_serializer(dividends, many=True)
            return Response(serializer.data)

        return Response([])

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def group_dividends(self, request):
        """Admin only: Get dividends by group"""
        group_id = request.query_params.get('group_id')
        period_id = request.query_params.get('period_id')

        if group_id:
            dividends = MemberDividend.objects.filter(member__group_id=group_id)
            if period_id:
                dividends = dividends.filter(dividend_period_id=period_id)
            serializer = self.get_serializer(dividends, many=True)
            return Response(serializer.data)
        return Response([])

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def group_report(self, request, pk=None):
        """Generate comprehensive dividend report for a specific group"""
        period = self.get_object()
        group_id = request.query_params.get('group_id')

        if not group_id:
            return Response({
                'status': 'error',
                'message': 'group_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)

        report = period.generate_group_dividends_report(group)
        previous_payments = period.get_previous_payments_for_group(group)

        return Response({
            'period': DividendPeriodSerializer(period).data,
            'group': {
                'id': group.id,
                'name': group.name,
                'location': group.location
            },
            'report': report,
            'previous_payments': previous_payments
        })

# Legacy viewset for backward compatibility
class DividendViewSet(viewsets.ModelViewSet):
    queryset = Dividend.objects.all()
    serializer_class = DividendSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own dividends
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically set the user to the current user
        serializer.save(user=self.request.user)

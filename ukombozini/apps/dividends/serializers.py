from rest_framework import serializers
from .models import DividendPeriod, MemberDividend, DividendDistribution, Dividend

class DividendPeriodSerializer(serializers.ModelSerializer):
    is_current_december = serializers.BooleanField(read_only=True)
    can_calculate = serializers.BooleanField(read_only=True)

    class Meta:
        model = DividendPeriod
        fields = '__all__'
        read_only_fields = [
            'calculation_date', 'net_profit', 'total_dividend_pool',
            'reserve_amount', 'development_amount', 'is_current_december'
        ]

    def validate_year(self, value):
        """Ensure year is not in the future"""
        from datetime import date
        if value > date.today().year:
            raise serializers.ValidationError("Cannot create dividend period for future years")
        return value

class MemberDividendSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    member_group = serializers.CharField(source='member.group.name', read_only=True)
    period_year = serializers.IntegerField(source='dividend_period.year', read_only=True)
    is_visible_to_field_officer = serializers.BooleanField(read_only=True)
    is_visible_to_member = serializers.BooleanField(read_only=True)

    class Meta:
        model = MemberDividend
        fields = '__all__'

class DividendDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DividendDistribution
        fields = '__all__'

class DividendCalculationSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    reserve_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    development_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    dividend_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, default=70.00)

# Legacy serializer for backward compatibility
class DividendSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Dividend
        fields = ['id', 'user', 'user_username', 'amount', 'date', 'description']
        read_only_fields = ['id']

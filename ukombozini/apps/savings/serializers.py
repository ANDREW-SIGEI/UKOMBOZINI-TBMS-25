from rest_framework import serializers
from django.utils import timezone
from .models import SavingsTransaction

class SavingsTransactionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)

    class Meta:
        model = SavingsTransaction
        fields = [
            'id', 'member', 'member_name', 'group', 'group_name', 'amount',
            'transaction_type', 'reference', 'transaction_date', 'balance_after',
            'recorded_by', 'recorded_by_name', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_transaction_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Transaction date cannot be in the future")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['recorded_by'] = request.user
        return super().create(validated_data)

class SavingsTransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsTransaction
        fields = [
            'member', 'group', 'amount', 'transaction_type', 'reference',
            'transaction_date', 'notes'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['recorded_by'] = request.user
        return super().create(validated_data)

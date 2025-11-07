from rest_framework import serializers
from .models import Dividend

class DividendSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Dividend
        fields = ['id', 'user', 'user_username', 'amount', 'date', 'description']
        read_only_fields = ['id']

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, UserActivity

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = (
            'username', 'password', 'password2', 'email', 'first_name', 'last_name',
            'user_type', 'phone_number', 'id_number', 'assigned_county',
            'assigned_constituency', 'assigned_ward'
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        if CustomUser.objects.filter(id_number=attrs.get('id_number')).exists():
            raise serializers.ValidationError({"id_number": "A user with this ID number already exists."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'user_type_display', 'phone_number', 'id_number',
            'profile_picture', 'assigned_county', 'assigned_constituency',
            'assigned_ward', 'is_active', 'date_joined', 'last_activity',
            'last_location'
        )
        read_only_fields = ('id', 'date_joined', 'last_activity')

    def get_full_name(self, obj):
        return obj.get_full_name()

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'email', 'phone_number',
            'profile_picture', 'assigned_county', 'assigned_constituency',
            'assigned_ward'
        )

class UserActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ('timestamp',)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs

class LocationUpdateSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    address = serializers.CharField(required=False)

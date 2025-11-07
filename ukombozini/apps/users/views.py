from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from .models import CustomUser, UserActivity
from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserUpdateSerializer,
    UserActivitySerializer, ChangePasswordSerializer, LocationUpdateSerializer
)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_user_activity(user, action, description, request=None, content_type=None, object_id=None):
    """Utility function to log user activities"""
    ip_address = get_client_ip(request) if request else None
    user_agent = request.META.get('HTTP_USER_AGENT') if request else None

    UserActivity.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        content_type=content_type,
        object_id=object_id
    )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.is_active:
            # Update last activity
            user.last_activity = timezone.now()
            user.save()

            # Log login activity
            log_user_activity(
                user=user,
                action='login',
                description=f'User {user.username} logged in successfully',
                request=request
            )

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        else:
            return Response(
                {'error': 'Account is disabled. Please contact administrator.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        return Response(
            {'error': 'Invalid username or password'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Log registration activity
        log_user_activity(
            user=user,
            action='create',
            description=f'New user {user.username} registered as {user.get_user_type_display()}',
            request=request
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_view(request):
    if request.user.is_authenticated:
        # Log logout activity
        log_user_activity(
            user=request.user,
            action='logout',
            description=f'User {request.user.username} logged out',
            request=request
        )

    return Response({'message': 'Successfully logged out'})

@api_view(['POST'])
def update_location(request):
    """Update officer's current location"""
    serializer = LocationUpdateSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        latitude = serializer.validated_data['latitude']
        longitude = serializer.validated_data['longitude']
        address = serializer.validated_data.get('address', '')

        # Update user's last location
        user.last_location = f"{latitude},{longitude} - {address}"
        user.save()

        # Log location update
        log_user_activity(
            user=user,
            action='location_update',
            description=f'Location updated to {address} ({latitude}, {longitude})',
            request=request
        )

        return Response({'message': 'Location updated successfully'})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Log profile update
        log_user_activity(
            user=request.user,
            action='update',
            description='User updated their profile information',
            request=request
        )
        return super().update(request, *args, **kwargs)

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()

        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': ['Wrong password.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Log password change
        log_user_activity(
            user=user,
            action='update',
            description='User changed their password',
            request=request
        )

        return Response({'message': 'Password updated successfully'})

class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin can see all users
        if user.user_type == 'admin':
            return CustomUser.objects.all()

        # Field officers can see other field officers and their group members
        elif user.user_type == 'field_officer':
            return CustomUser.objects.filter(
                Q(user_type='field_officer') |
                Q(user_type='group_admin') |
                Q(user_type='member')
            )

        # Others can only see themselves
        return CustomUser.objects.filter(id=user.id)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'admin':
            return CustomUser.objects.all()
        elif user.user_type == 'field_officer':
            return CustomUser.objects.filter(
                Q(user_type='field_officer') |
                Q(user_type='group_admin') |
                Q(user_type='member')
            )
        return CustomUser.objects.filter(id=user.id)

    def perform_destroy(self, instance):
        # Log user deletion
        log_user_activity(
            user=self.request.user,
            action='delete',
            description=f'Deleted user {instance.username}',
            request=self.request,
            content_type='user',
            object_id=str(instance.id)
        )
        instance.delete()

    def perform_update(self, serializer):
        instance = serializer.save()

        # Log user update
        log_user_activity(
            user=self.request.user,
            action='update',
            description=f'Updated user {instance.username}',
            request=self.request,
            content_type='user',
            object_id=str(instance.id)
        )

class OfficerListView(generics.ListAPIView):
    """List all field officers (admin only)"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type != 'admin':
            return CustomUser.objects.none()

        return CustomUser.objects.filter(user_type='field_officer')

class UserActivityView(generics.ListAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin can see all activities
        if user.user_type == 'admin':
            return UserActivity.objects.all()

        # Field officers can see their own activities and activities of users they manage
        elif user.user_type == 'field_officer':
            managed_users = CustomUser.objects.filter(
                Q(user_type='group_admin') | Q(user_type='member')
            )
            return UserActivity.objects.filter(
                Q(user=user) | Q(user__in=managed_users)
            )

        # Others can only see their own activities
        return UserActivity.objects.filter(user=user)

class OfficerActivityView(generics.ListAPIView):
    """Get activities for specific officer (admin only)"""
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type != 'admin':
            return UserActivity.objects.none()

        officer_id = self.kwargs['officer_id']
        return UserActivity.objects.filter(user_id=officer_id)

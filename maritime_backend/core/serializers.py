from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vessel, Port, Voyage, Notification, Event

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text='Password must be at least 8 characters long'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {
            'email': {'required': True},
            'role': {'required': False}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']
        read_only_fields = ['id', 'username', 'email', 'role']


class DashboardSerializer(serializers.Serializer):
    total_vessels = serializers.IntegerField()
    total_ports = serializers.IntegerField()
    total_voyages = serializers.IntegerField()


class VesselSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vessel
        fields = [
            'id',
            'imo_number',
            'name',
            'vessel_type',
            'flag',
            'cargo_type',
            'operator',
            'last_position_lat',
            'last_position_lon',
            'last_update',
        ]
        read_only_fields = fields


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to subscribe/create a notification entry for a vessel.
    Event is optional for generic vessel alerts.
    """

    class Meta:
        model = Notification
        fields = ['id', 'vessel', 'event', 'notification_type', 'message']
        read_only_fields = ['id']

    def create(self, validated_data):
        user = self.context['request'].user
        return Notification.objects.create(user=user, **validated_data)


class PortCongestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = [
            'id',
            'name',
            'location',
            'country',
            'congestion_score',
            'avg_wait_time',
            'last_update',
        ]
        read_only_fields = fields


class EventSerializer(serializers.ModelSerializer):
    vessel_name = serializers.CharField(source='vessel.name', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'vessel',
            'vessel_name',
            'event_type',
            'location',
            'timestamp',
            'details',
        ]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    vessel_name = serializers.CharField(source='vessel.name', read_only=True)
    event_type = serializers.CharField(source='event.event_type', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'vessel',
            'vessel_name',
            'event',
            'event_type',
            'message',
            'notification_type',
            'is_read',
            'timestamp',
        ]
        read_only_fields = fields


class LiveVesselSerializer(serializers.Serializer):
    """
    Serializer for live vessel position data from AIS sources.
    """
    imo = serializers.CharField(max_length=50, help_text='IMO number')
    name = serializers.CharField(max_length=255, help_text='Vessel name')
    vessel_type = serializers.CharField(max_length=100, help_text='Type of vessel')
    latitude = serializers.FloatField(help_text='Current latitude')
    longitude = serializers.FloatField(help_text='Current longitude')
    speed = serializers.FloatField(help_text='Speed in knots')
    heading = serializers.IntegerField(help_text='Heading in degrees (0-359)')
    timestamp = serializers.DateTimeField(help_text='Timestamp of last position update')

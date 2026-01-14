from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vessel, Port, Voyage, Notification, Event, VesselSubscription

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
            'mmsi',
            'name',
            'vessel_type',
            'flag',
            'cargo_type',
            'operator',
            'last_position_lat',
            'last_position_lon',
            'speed',
            'heading',
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
    arrivals = serializers.IntegerField(source='arrivals_count', read_only=True)
    departures = serializers.IntegerField(source='departures_count', read_only=True)
    
    class Meta:
        model = Port
        fields = [
            'name',
            'country',
            'congestion_score',
            'avg_wait_time',
            'arrivals',
            'departures',
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
    mmsi = serializers.CharField(max_length=20, required=False, help_text='MMSI number')
    name = serializers.CharField(max_length=255, help_text='Vessel name')
    vessel_type = serializers.CharField(max_length=100, help_text='Type of vessel')
    flag = serializers.CharField(max_length=50, required=False, help_text='Flag state')
    latitude = serializers.FloatField(help_text='Current latitude')
    longitude = serializers.FloatField(help_text='Current longitude')
    speed = serializers.FloatField(help_text='Speed in knots')
    heading = serializers.IntegerField(help_text='Heading in degrees (0-359)')
    timestamp = serializers.DateTimeField(help_text='Timestamp of last position update')


class VesselSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for vessel subscription management.
    """
    vessel_name = serializers.CharField(source='vessel.name', read_only=True)
    vessel_imo = serializers.CharField(source='vessel.imo_number', read_only=True)
    
    class Meta:
        model = VesselSubscription
        fields = [
            'id',
            'vessel',
            'vessel_name',
            'vessel_imo',
            'subscription_type',
            'notify_storm_zones',
            'notify_piracy_zones',
            'notify_congestion',
            'notify_position_updates',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'vessel_name', 'vessel_imo', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create subscription for the authenticated user."""
        user = self.context['request'].user
        return VesselSubscription.objects.create(user=user, **validated_data)
    
    def validate(self, data):
        """Validate subscription data."""
        user = self.context['request'].user
        vessel = data.get('vessel')
        
        # Check if subscription already exists (for create operations)
        if not self.instance and VesselSubscription.objects.filter(user=user, vessel=vessel).exists():
            raise serializers.ValidationError("You are already subscribed to this vessel.")
        
        return data


class VesselSubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating vessel subscriptions.
    """
    class Meta:
        model = VesselSubscription
        fields = [
            'vessel',
            'subscription_type',
            'notify_storm_zones',
            'notify_piracy_zones',
            'notify_congestion',
            'notify_position_updates',
        ]
    
    def create(self, validated_data):
        """Create subscription for the authenticated user."""
        user = self.context['request'].user
        
        # Check if subscription already exists
        vessel = validated_data['vessel']
        existing_subscription = VesselSubscription.objects.filter(user=user, vessel=vessel).first()
        
        if existing_subscription:
            # Update existing subscription instead of creating new one
            for field, value in validated_data.items():
                setattr(existing_subscription, field, value)
            existing_subscription.is_active = True
            existing_subscription.save()
            return existing_subscription
        
        return VesselSubscription.objects.create(user=user, **validated_data)


class VesselSubscriptionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing user's vessel subscriptions.
    """
    vessel_name = serializers.CharField(source='vessel.name', read_only=True)
    vessel_imo = serializers.CharField(source='vessel.imo_number', read_only=True)
    vessel_type = serializers.CharField(source='vessel.vessel_type', read_only=True)
    vessel_flag = serializers.CharField(source='vessel.flag', read_only=True)
    
    class Meta:
        model = VesselSubscription
        fields = [
            'id',
            'vessel',
            'vessel_name',
            'vessel_imo',
            'vessel_type',
            'vessel_flag',
            'subscription_type',
            'notify_storm_zones',
            'notify_piracy_zones',
            'notify_congestion',
            'notify_position_updates',
            'is_active',
            'created_at',
        ]
        read_only_fields = fields


class PortAnalyticsSummarySerializer(serializers.Serializer):
    """
    Serializer for port analytics summary data.
    """
    total_ports = serializers.IntegerField()
    average_congestion_score = serializers.FloatField()
    average_wait_time = serializers.FloatField()
    total_arrivals = serializers.IntegerField()
    total_departures = serializers.IntegerField()


class CongestionDistributionSerializer(serializers.Serializer):
    """
    Serializer for congestion level distribution.
    """
    critical = serializers.IntegerField()
    high = serializers.IntegerField()
    moderate = serializers.IntegerField()
    low = serializers.IntegerField()


class TopCongestedPortSerializer(serializers.Serializer):
    """
    Serializer for top congested ports data.
    """
    name = serializers.CharField()
    country = serializers.CharField()
    congestion_score = serializers.FloatField()
    avg_wait_time = serializers.FloatField()
    arrivals_count = serializers.IntegerField()
    departures_count = serializers.IntegerField()


class RecentEventSerializer(serializers.Serializer):
    """
    Serializer for recent congestion events.
    """
    vessel_name = serializers.CharField()
    vessel_imo = serializers.CharField()
    location = serializers.CharField()
    timestamp = serializers.DateTimeField()
    details = serializers.CharField()


class PortDashboardSerializer(serializers.Serializer):
    """
    Serializer for comprehensive port dashboard data.
    """
    summary = PortAnalyticsSummarySerializer()
    congestion_distribution = CongestionDistributionSerializer()
    top_congested_ports = TopCongestedPortSerializer(many=True)
    recent_events = RecentEventSerializer(many=True)
    thresholds = serializers.DictField()
    last_updated = serializers.DateTimeField()
    note = serializers.CharField(required=False)


class PortAnalyticsRefreshSerializer(serializers.Serializer):
    """
    Serializer for port analytics refresh operation results.
    """
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(required=False)
    unctad_records_fetched = serializers.IntegerField()
    ports_updated = serializers.IntegerField()
    ports_not_found = serializers.IntegerField()
    events_created = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField(), required=False)
    success = serializers.BooleanField()
    error = serializers.CharField(required=False)


class VesselPositionSerializer(serializers.Serializer):
    """
    Serializer for vessel position data.
    """
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    speed = serializers.FloatField(required=False, allow_null=True)
    heading = serializers.IntegerField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField()
    source = serializers.CharField()
    accuracy = serializers.FloatField(required=False, allow_null=True)
    is_interpolated = serializers.BooleanField()
    voyage_id = serializers.IntegerField(required=False, allow_null=True)


class VoyageRouteSerializer(serializers.Serializer):
    """
    Serializer for voyage route data.
    """
    voyage = serializers.DictField()
    route = VesselPositionSerializer(many=True)
    total_positions = serializers.IntegerField()
    include_interpolated = serializers.BooleanField()


class VoyageReplayPositionSerializer(serializers.Serializer):
    """
    Serializer for voyage replay position data.
    """
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    speed = serializers.FloatField(required=False, allow_null=True)
    heading = serializers.IntegerField(required=False, allow_null=True)
    timestamp = serializers.CharField(required=False, allow_null=True)
    time_offset_seconds = serializers.FloatField()
    replay_time_seconds = serializers.FloatField()
    distance_from_previous = serializers.FloatField()
    source = serializers.CharField()
    is_interpolated = serializers.BooleanField()


class VoyageReplaySerializer(serializers.Serializer):
    """
    Serializer for voyage replay data.
    """
    voyage = serializers.DictField()
    replay_settings = serializers.DictField()
    metadata = serializers.DictField()
    positions = VoyageReplayPositionSerializer(many=True)
    generated_at = serializers.DateTimeField()


class VesselHistorySerializer(serializers.Serializer):
    """
    Serializer for vessel historical data.
    """
    vessel = serializers.DictField()
    date_range = serializers.DictField()
    positions = VesselPositionSerializer(many=True)
    voyages = serializers.DictField()
    total_positions = serializers.IntegerField()
    has_more = serializers.BooleanField()


class VoyageStatisticsSerializer(serializers.Serializer):
    """
    Serializer for voyage statistics.
    """
    voyage_id = serializers.IntegerField()
    vessel_name = serializers.CharField()
    route = serializers.CharField()
    status = serializers.CharField()
    statistics = serializers.DictField()


class VoyageAuditLogSerializer(serializers.Serializer):
    """
    Serializer for voyage audit log entries.
    """
    id = serializers.IntegerField()
    action = serializers.CharField()
    description = serializers.CharField()
    user = serializers.CharField()
    timestamp = serializers.DateTimeField()
    ip_address = serializers.CharField(required=False, allow_null=True)
    metadata = serializers.DictField()
    compliance_category = serializers.CharField(required=False, allow_null=True)


class RecordPositionSerializer(serializers.Serializer):
    """
    Serializer for recording vessel positions.
    """
    vessel_id = serializers.IntegerField()
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    timestamp = serializers.DateTimeField()
    speed = serializers.FloatField(required=False, allow_null=True, min_value=0)
    heading = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=359)
    source = serializers.CharField(default='MANUAL', max_length=50)
    accuracy = serializers.FloatField(required=False, allow_null=True, min_value=0)

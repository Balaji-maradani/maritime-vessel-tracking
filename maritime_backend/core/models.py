from django.db import models

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('OPERATOR', 'Operator'),
        ('ANALYST', 'Analyst'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='OPERATOR',
        verbose_name='Role',
        help_text='User role in the system'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"



class Vessel(models.Model):
    imo_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='IMO Number',
        help_text='International Maritime Organization number'
    )
    mmsi = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='MMSI',
        help_text='Maritime Mobile Service Identity'
    )
    name = models.CharField(max_length=255, verbose_name='Vessel Name')
    vessel_type = models.CharField(max_length=50, verbose_name='Vessel Type')
    flag = models.CharField(max_length=50, verbose_name='Flag State')
    cargo_type = models.CharField(max_length=50, verbose_name='Cargo Type')
    operator = models.CharField(max_length=255, verbose_name='Operator')
    last_position_lat = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Last Position Latitude'
    )
    last_position_lon = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Last Position Longitude'
    )
    speed = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Speed',
        help_text='Speed in knots'
    )
    heading = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Heading',
        help_text='Heading in degrees (0-359)'
    )
    last_update = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Update'
    )

    class Meta:
        verbose_name = 'Vessel'
        verbose_name_plural = 'Vessels'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.imo_number})"


class Port(models.Model):
    name = models.CharField(max_length=255, verbose_name='Port Name')
    location = models.CharField(max_length=255, verbose_name='Location')
    country = models.CharField(max_length=100, verbose_name='Country')
    congestion_score = models.FloatField(
        verbose_name='Congestion Score',
        help_text='Port congestion score (0-10)'
    )
    avg_wait_time = models.FloatField(
        verbose_name='Average Wait Time',
        help_text='Average wait time in hours'
    )
    arrivals_count = models.IntegerField(
        default=0,
        verbose_name='Arrivals Count',
        help_text='Number of vessel arrivals'
    )
    departures_count = models.IntegerField(
        default=0,
        verbose_name='Departures Count',
        help_text='Number of vessel departures'
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Updated'
    )

    class Meta:
        verbose_name = 'Port'
        verbose_name_plural = 'Ports'
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.country}"


class Voyage(models.Model):
    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    vessel = models.ForeignKey(
        Vessel,
        on_delete=models.CASCADE,
        related_name='voyages',
        verbose_name='Vessel'
    )
    port_from = models.ForeignKey(
        Port,
        related_name="departures",
        on_delete=models.CASCADE,
        verbose_name='Port of Departure'
    )
    port_to = models.ForeignKey(
        Port,
        related_name="arrivals",
        on_delete=models.CASCADE,
        verbose_name='Port of Arrival'
    )
    departure_time = models.DateTimeField(verbose_name='Departure Time')
    arrival_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Arrival Time'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='PLANNED',
        verbose_name='Status'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        verbose_name = 'Voyage'
        verbose_name_plural = 'Voyages'
        ordering = ['-departure_time']

    def __str__(self):
        return f"{self.vessel.name} voyage: {self.port_from.name} → {self.port_to.name}"


class Event(models.Model):
    EVENT_TYPE_CHOICES = (
        ('ARRIVAL', 'Arrival'),
        ('DEPARTURE', 'Departure'),
        ('ANCHORAGE', 'Anchorage'),
        ('BERTHING', 'Berthing'),
        ('CARGO_OPERATION', 'Cargo Operation'),
        ('INCIDENT', 'Incident'),
        ('WEATHER_ALERT', 'Weather Alert'),
        ('HIGH_CONGESTION', 'High Port Congestion'),
        ('STORM_ENTRY', 'Storm Zone Entry'),
        ('PIRACY_RISK', 'Piracy Risk Zone Entry'),
        ('OTHER', 'Other'),
    )

    vessel = models.ForeignKey(
        Vessel,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Vessel'
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        verbose_name='Event Type'
    )
    location = models.CharField(max_length=255, verbose_name='Location')
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Timestamp'
    )
    details = models.TextField(verbose_name='Details', blank=True)

    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.vessel.name} ({self.timestamp})"


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ('VOYAGE_UPDATE', 'Voyage Update'),
        ('EVENT_ALERT', 'Event Alert'),
        ('POSITION_UPDATE', 'Position Update'),
        ('SYSTEM_ALERT', 'System Alert'),
        ('OTHER', 'Other'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='User'
    )
    vessel = models.ForeignKey(
        Vessel,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Vessel'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name='Event'
    )
    message = models.TextField(verbose_name='Message')
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name='Notification Type'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Is Read'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Timestamp'
    )

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()}"


class VesselSubscription(models.Model):
    """
    Model to track user subscriptions to specific vessels for notifications.
    """
    SUBSCRIPTION_TYPE_CHOICES = (
        ('ALL_EVENTS', 'All Events'),
        ('SAFETY_ONLY', 'Safety Events Only'),
        ('POSITION_UPDATES', 'Position Updates Only'),
        ('CUSTOM', 'Custom Events'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vessel_subscriptions',
        verbose_name='User'
    )
    vessel = models.ForeignKey(
        Vessel,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Vessel'
    )
    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TYPE_CHOICES,
        default='ALL_EVENTS',
        verbose_name='Subscription Type'
    )
    notify_storm_zones = models.BooleanField(
        default=True,
        verbose_name='Notify Storm Zone Entry'
    )
    notify_piracy_zones = models.BooleanField(
        default=True,
        verbose_name='Notify Piracy Zone Entry'
    )
    notify_congestion = models.BooleanField(
        default=True,
        verbose_name='Notify Congestion Risk'
    )
    notify_position_updates = models.BooleanField(
        default=False,
        verbose_name='Notify Position Updates'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Vessel Subscription'
        verbose_name_plural = 'Vessel Subscriptions'
        unique_together = ('user', 'vessel')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} subscribed to {self.vessel.name}"


class VesselPosition(models.Model):
    """
    Model to store historical vessel positions for voyage tracking and replay.
    Optimized for storage with indexed queries.
    """
    vessel = models.ForeignKey(
        Vessel,
        on_delete=models.CASCADE,
        related_name='positions',
        verbose_name='Vessel',
        db_index=True
    )
    voyage = models.ForeignKey(
        'Voyage',
        on_delete=models.CASCADE,
        related_name='positions',
        verbose_name='Voyage',
        null=True,
        blank=True,
        db_index=True
    )
    latitude = models.FloatField(
        verbose_name='Latitude',
        help_text='Position latitude in decimal degrees'
    )
    longitude = models.FloatField(
        verbose_name='Longitude',
        help_text='Position longitude in decimal degrees'
    )
    speed = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Speed',
        help_text='Speed in knots'
    )
    heading = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Heading',
        help_text='Heading in degrees (0-359)'
    )
    timestamp = models.DateTimeField(
        verbose_name='Position Timestamp',
        db_index=True,
        help_text='When this position was recorded'
    )
    source = models.CharField(
        max_length=50,
        default='AIS',
        verbose_name='Data Source',
        help_text='Source of position data (AIS, GPS, Manual, etc.)'
    )
    accuracy = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Position Accuracy',
        help_text='Position accuracy in meters'
    )
    is_interpolated = models.BooleanField(
        default=False,
        verbose_name='Is Interpolated',
        help_text='Whether this position was interpolated between actual readings'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    class Meta:
        verbose_name = 'Vessel Position'
        verbose_name_plural = 'Vessel Positions'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vessel', 'timestamp']),
            models.Index(fields=['voyage', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['vessel', 'voyage']),
        ]
        unique_together = ('vessel', 'timestamp')  # Prevent duplicate positions

    def __str__(self):
        return f"{self.vessel.name} at {self.latitude:.4f}, {self.longitude:.4f} on {self.timestamp}"

    @property
    def coordinates(self):
        """Return coordinates as a tuple for easy access."""
        return (self.latitude, self.longitude)

    def distance_to(self, other_position):
        """
        Calculate distance to another position using Haversine formula.
        Returns distance in nautical miles.
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [
            self.latitude, self.longitude,
            other_position.latitude, other_position.longitude
        ])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in nautical miles
        r = 3440.065
        
        return c * r


class VoyageAuditLog(models.Model):
    """
    Model for audit and compliance logging of voyage-related activities.
    Tracks all significant events and data access for regulatory compliance.
    """
    ACTION_CHOICES = (
        ('VOYAGE_CREATED', 'Voyage Created'),
        ('VOYAGE_UPDATED', 'Voyage Updated'),
        ('VOYAGE_COMPLETED', 'Voyage Completed'),
        ('VOYAGE_CANCELLED', 'Voyage Cancelled'),
        ('POSITION_RECORDED', 'Position Recorded'),
        ('POSITION_UPDATED', 'Position Updated'),
        ('ROUTE_ACCESSED', 'Route Data Accessed'),
        ('REPLAY_STARTED', 'Voyage Replay Started'),
        ('REPLAY_COMPLETED', 'Voyage Replay Completed'),
        ('DATA_EXPORTED', 'Data Exported'),
        ('COMPLIANCE_CHECK', 'Compliance Check Performed'),
        ('ALERT_TRIGGERED', 'Alert Triggered'),
        ('USER_ACCESS', 'User Data Access'),
        ('SYSTEM_UPDATE', 'System Update'),
        ('DATA_RETENTION', 'Data Retention Action'),
    )

    voyage = models.ForeignKey(
        'Voyage',
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name='Voyage',
        null=True,
        blank=True,
        db_index=True
    )
    vessel = models.ForeignKey(
        Vessel,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name='Vessel',
        db_index=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        verbose_name='User',
        null=True,
        blank=True,
        db_index=True
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name='Action',
        db_index=True
    )
    description = models.TextField(
        verbose_name='Description',
        help_text='Detailed description of the action performed'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Address',
        help_text='IP address of the user or system performing the action'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='User Agent',
        help_text='User agent string for web requests'
    )
    metadata = models.JSONField(
        default=dict,
        verbose_name='Metadata',
        help_text='Additional metadata about the action'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Timestamp',
        db_index=True
    )
    compliance_category = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Compliance Category',
        help_text='Regulatory compliance category (SOLAS, MARPOL, etc.)'
    )
    retention_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Retention Date',
        help_text='Date when this log entry should be archived/deleted'
    )

    class Meta:
        verbose_name = 'Voyage Audit Log'
        verbose_name_plural = 'Voyage Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vessel', 'timestamp']),
            models.Index(fields=['voyage', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['compliance_category', 'timestamp']),
            models.Index(fields=['retention_date']),
        ]

    def __str__(self):
        return f"{self.action} - {self.vessel.name} by {self.user or 'System'} at {self.timestamp}"

    @classmethod
    def log_action(cls, vessel, action, description, user=None, voyage=None, 
                   ip_address=None, user_agent=None, metadata=None, 
                   compliance_category=None):
        """
        Convenience method to create audit log entries.
        """
        return cls.objects.create(
            vessel=vessel,
            voyage=voyage,
            user=user,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            compliance_category=compliance_category
        )

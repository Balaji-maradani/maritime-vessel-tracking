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
    last_update = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Update'
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

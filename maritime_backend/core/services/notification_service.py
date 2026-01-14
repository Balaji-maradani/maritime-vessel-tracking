"""
Event-driven notification service for maritime analytics.

Handles automatic notification generation for:
- High congestion ports
- Storm zone entry
- Piracy risk zone entry
"""

import logging
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

from core.models import User, Vessel, Event, Notification, Port, VesselSubscription

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service class for managing event-driven notifications.
    """
    
    @staticmethod
    def create_notification(
        user: User,
        vessel: Vessel,
        event: Event,
        message: str,
        notification_type: str = 'EVENT_ALERT'
    ) -> Notification:
        """
        Create a single notification record.
        """
        return Notification.objects.create(
            user=user,
            vessel=vessel,
            event=event,
            message=message,
            notification_type=notification_type,
            is_read=False
        )
    
    @staticmethod
    def notify_users_for_event(
        event: Event,
        user_roles: List[str] = None,
        specific_users: List[User] = None
    ) -> int:
        """
        Create notifications for relevant users when an event occurs.
        Now includes vessel subscription-based notifications.
        
        Args:
            event: The event that triggered the notification
            user_roles: List of user roles to notify (default: ['ADMIN', 'OPERATOR'])
            specific_users: Specific users to notify (overrides role-based selection)
        
        Returns:
            Number of notifications created
        """
        notifications_created = 0
        
        # First, notify subscribed users for vessel-specific events
        if event.event_type in ['STORM_ENTRY', 'PIRACY_RISK', 'HIGH_CONGESTION']:
            notifications_created += NotificationService._notify_subscribed_users(event)
        
        # Then, notify users based on roles (existing functionality)
        if specific_users:
            users = specific_users
        else:
            if user_roles is None:
                user_roles = ['ADMIN', 'OPERATOR']
            users = User.objects.filter(role__in=user_roles)
        
        if users.exists():
            # Generate appropriate message based on event type
            message = NotificationService._generate_message(event)
            
            # Bulk create notifications for role-based users
            role_notifications = [
                Notification(
                    user=user,
                    vessel=event.vessel,
                    event=event,
                    message=message,
                    notification_type='EVENT_ALERT',
                    is_read=False
                )
                for user in users
            ]
            
            created_notifications = Notification.objects.bulk_create(role_notifications)
            notifications_created += len(created_notifications)
        
        logger.info(f"Created {notifications_created} notifications for event {event.id}")
        return notifications_created
    
    @staticmethod
    def _notify_subscribed_users(event: Event) -> int:
        """
        Notify users who are subscribed to the specific vessel for this event type.
        
        Args:
            event: The event that occurred
            
        Returns:
            Number of subscription-based notifications created
        """
        # Get active subscriptions for this vessel
        subscriptions = VesselSubscription.objects.filter(
            vessel=event.vessel,
            is_active=True
        )
        
        # Filter subscriptions based on event type and user preferences
        relevant_subscriptions = []
        for subscription in subscriptions:
            should_notify = False
            
            if event.event_type == 'STORM_ENTRY' and subscription.notify_storm_zones:
                should_notify = True
            elif event.event_type == 'PIRACY_RISK' and subscription.notify_piracy_zones:
                should_notify = True
            elif event.event_type == 'HIGH_CONGESTION' and subscription.notify_congestion:
                should_notify = True
            elif event.event_type == 'POSITION_UPDATE' and subscription.notify_position_updates:
                should_notify = True
            elif subscription.subscription_type == 'ALL_EVENTS':
                should_notify = True
            
            if should_notify:
                relevant_subscriptions.append(subscription)
        
        if not relevant_subscriptions:
            return 0
        
        # Generate personalized message
        message = NotificationService._generate_subscription_message(event)
        
        # Create notifications for subscribed users
        subscription_notifications = [
            Notification(
                user=subscription.user,
                vessel=event.vessel,
                event=event,
                message=message,
                notification_type='EVENT_ALERT',
                is_read=False
            )
            for subscription in relevant_subscriptions
        ]
        
        created_notifications = Notification.objects.bulk_create(subscription_notifications)
        logger.info(f"Created {len(created_notifications)} subscription-based notifications for event {event.id}")
        
        return len(created_notifications)
    
    @staticmethod
    def _generate_subscription_message(event: Event) -> str:
        """
        Generate personalized notification message for subscribed users.
        
        Args:
            event: The event that occurred
            
        Returns:
            Personalized notification message
        """
        vessel_name = event.vessel.name
        
        subscription_message_templates = {
            'STORM_ENTRY': f"🌩️ Your subscribed vessel {vessel_name} has entered a storm zone at {event.location}. Monitor weather conditions closely.",
            'PIRACY_RISK': f"🚨 Your subscribed vessel {vessel_name} has entered a piracy risk zone at {event.location}. Enhanced security measures recommended.",
            'HIGH_CONGESTION': f"🚢 Your subscribed vessel {vessel_name} is approaching a high congestion port: {event.location}. Expect potential delays.",
            'POSITION_UPDATE': f"📍 Position update for your subscribed vessel {vessel_name} at {event.location}.",
        }
        
        return subscription_message_templates.get(
            event.event_type,
            f"📢 Update for your subscribed vessel {vessel_name}: {event.details}"
        )
    
    @staticmethod
    def _generate_message(event: Event) -> str:
        """
        Generate appropriate notification message based on event type.
        """
        vessel_name = event.vessel.name
        event_type = event.get_event_type_display()
        
        message_templates = {
            'HIGH_CONGESTION': f"🚨 {vessel_name} is approaching a high congestion port: {event.location}",
            'STORM_ENTRY': f"⛈️ {vessel_name} has entered a storm zone at {event.location}",
            'PIRACY_RISK': f"🏴‍☠️ {vessel_name} has entered a piracy risk zone at {event.location}",
            'WEATHER_ALERT': f"🌪️ Weather alert for {vessel_name} at {event.location}",
            'INCIDENT': f"⚠️ Incident reported for {vessel_name} at {event.location}",
        }
        
        return message_templates.get(
            event.event_type,
            f"📢 {event_type} alert for {vessel_name}: {event.details}"
        )


class EventTriggerService:
    """
    Service for detecting and triggering events based on various conditions.
    """
    
    @staticmethod
    def check_port_congestion() -> Dict[str, Any]:
        """
        Check for high congestion ports and create events for vessels approaching them.
        
        Returns:
            Summary of events and notifications created
        """
        high_congestion_threshold = 7.0  # Configurable threshold
        
        # Find ports with high congestion
        congested_ports = Port.objects.filter(
            congestion_score__gte=high_congestion_threshold
        )
        
        events_created = 0
        notifications_created = 0
        
        for port in congested_ports:
            # Find vessels that might be approaching this port
            # This is a simplified approach - in reality you'd use more sophisticated logic
            nearby_vessels = Vessel.objects.filter(
                last_position_lat__isnull=False,
                last_position_lon__isnull=False,
                # Add proximity logic here based on your requirements
            )
            
            for vessel in nearby_vessels:
                # Check if we already have a recent congestion event for this vessel/port
                recent_event = Event.objects.filter(
                    vessel=vessel,
                    event_type='HIGH_CONGESTION',
                    location__icontains=port.name,
                    timestamp__gte=timezone.now() - timezone.timedelta(hours=6)
                ).exists()
                
                if not recent_event:
                    # Create high congestion event
                    event = Event.objects.create(
                        vessel=vessel,
                        event_type='HIGH_CONGESTION',
                        location=f"{port.name}, {port.country}",
                        details=f"Port congestion score: {port.congestion_score:.1f}, "
                               f"Average wait time: {port.avg_wait_time:.1f} hours"
                    )
                    events_created += 1
                    
                    # Create notifications
                    notifications_count = NotificationService.notify_users_for_event(event)
                    notifications_created += notifications_count
        
        return {
            'congested_ports': congested_ports.count(),
            'events_created': events_created,
            'notifications_created': notifications_created
        }
    
    @staticmethod
    def check_storm_zones(storm_zones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for vessels entering storm zones and create events.
        
        Args:
            storm_zones: List of storm zone data with coordinates and details
        
        Returns:
            Summary of events and notifications created
        """
        events_created = 0
        notifications_created = 0
        
        for zone in storm_zones:
            # Find vessels in this storm zone
            # This is simplified - you'd use proper geospatial queries in production
            vessels_in_zone = EventTriggerService._find_vessels_in_zone(
                zone.get('coordinates', []),
                zone.get('center_lat'),
                zone.get('center_lon'),
                zone.get('radius', 50)  # km
            )
            
            for vessel in vessels_in_zone:
                # Check if we already have a recent storm event for this vessel
                recent_event = Event.objects.filter(
                    vessel=vessel,
                    event_type='STORM_ENTRY',
                    timestamp__gte=timezone.now() - timezone.timedelta(hours=3)
                ).exists()
                
                if not recent_event:
                    event = Event.objects.create(
                        vessel=vessel,
                        event_type='STORM_ENTRY',
                        location=f"Storm Zone - Lat: {vessel.last_position_lat:.3f}, "
                               f"Lon: {vessel.last_position_lon:.3f}",
                        details=f"Vessel entered storm zone. Severity: {zone.get('severity', 'Unknown')}, "
                               f"Wind speed: {zone.get('wind_speed', 'Unknown')} km/h"
                    )
                    events_created += 1
                    
                    # Create notifications with higher priority for storm events
                    notifications_count = NotificationService.notify_users_for_event(
                        event, 
                        user_roles=['ADMIN', 'OPERATOR', 'ANALYST']
                    )
                    notifications_created += notifications_count
        
        return {
            'storm_zones_checked': len(storm_zones),
            'events_created': events_created,
            'notifications_created': notifications_created
        }
    
    @staticmethod
    def check_piracy_zones(piracy_zones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for vessels entering piracy risk zones and create events.
        
        Args:
            piracy_zones: List of piracy zone data with coordinates and risk levels
        
        Returns:
            Summary of events and notifications created
        """
        events_created = 0
        notifications_created = 0
        
        for zone in piracy_zones:
            # Find vessels in this piracy risk zone
            vessels_in_zone = EventTriggerService._find_vessels_in_zone(
                zone.get('coordinates', []),
                zone.get('center_lat'),
                zone.get('center_lon'),
                zone.get('radius', 100)  # km
            )
            
            for vessel in vessels_in_zone:
                # Check if we already have a recent piracy risk event for this vessel
                recent_event = Event.objects.filter(
                    vessel=vessel,
                    event_type='PIRACY_RISK',
                    timestamp__gte=timezone.now() - timezone.timedelta(hours=6)
                ).exists()
                
                if not recent_event:
                    event = Event.objects.create(
                        vessel=vessel,
                        event_type='PIRACY_RISK',
                        location=f"Piracy Risk Zone - Lat: {vessel.last_position_lat:.3f}, "
                               f"Lon: {vessel.last_position_lon:.3f}",
                        details=f"Vessel entered piracy risk zone. Risk level: {zone.get('risk_level', 'Unknown')}, "
                               f"Last incident: {zone.get('last_incident', 'Unknown')}"
                    )
                    events_created += 1
                    
                    # Create notifications for piracy risk
                    notifications_count = NotificationService.notify_users_for_event(event)
                    notifications_created += notifications_count
        
        return {
            'piracy_zones_checked': len(piracy_zones),
            'events_created': events_created,
            'notifications_created': notifications_created
        }
    
    @staticmethod
    def _find_vessels_in_zone(
        coordinates: List[List[float]], 
        center_lat: Optional[float], 
        center_lon: Optional[float], 
        radius_km: float
    ) -> List[Vessel]:
        """
        Find vessels within a specified zone.
        
        This is a simplified implementation using bounding box.
        In production, you'd use proper geospatial queries.
        """
        if center_lat is None or center_lon is None:
            return []
        
        # Convert radius from km to approximate degrees (rough approximation)
        radius_deg = radius_km / 111.0  # 1 degree ≈ 111 km
        
        return list(Vessel.objects.filter(
            last_position_lat__isnull=False,
            last_position_lon__isnull=False,
            last_position_lat__gte=center_lat - radius_deg,
            last_position_lat__lte=center_lat + radius_deg,
            last_position_lon__gte=center_lon - radius_deg,
            last_position_lon__lte=center_lon + radius_deg,
        ))


def run_all_event_checks() -> Dict[str, Any]:
    """
    Run all event checks and return a comprehensive summary.
    This function can be called by a scheduled task or API endpoint.
    """
    logger.info("Starting comprehensive event checks...")
    
    # Sample data for storm and piracy zones (in production, this would come from external APIs)
    sample_storm_zones = [
        {
            'center_lat': 25.0,
            'center_lon': 55.0,
            'radius': 50,
            'severity': 'High',
            'wind_speed': 85,
            'coordinates': [[24.0, 54.0], [24.0, 56.0], [26.0, 56.0], [26.0, 54.0]]
        }
    ]
    
    sample_piracy_zones = [
        {
            'center_lat': 12.0,
            'center_lon': 45.0,
            'radius': 100,
            'risk_level': 'High',
            'last_incident': '2024-01-05',
            'coordinates': [[10.0, 43.0], [10.0, 47.0], [14.0, 47.0], [14.0, 43.0]]
        }
    ]
    
    with transaction.atomic():
        # Check port congestion
        congestion_summary = EventTriggerService.check_port_congestion()
        
        # Check storm zones
        storm_summary = EventTriggerService.check_storm_zones(sample_storm_zones)
        
        # Check piracy zones
        piracy_summary = EventTriggerService.check_piracy_zones(sample_piracy_zones)
    
    total_summary = {
        'timestamp': timezone.now().isoformat(),
        'port_congestion': congestion_summary,
        'storm_zones': storm_summary,
        'piracy_zones': piracy_summary,
        'total_events_created': (
            congestion_summary['events_created'] + 
            storm_summary['events_created'] + 
            piracy_summary['events_created']
        ),
        'total_notifications_created': (
            congestion_summary['notifications_created'] + 
            storm_summary['notifications_created'] + 
            piracy_summary['notifications_created']
        )
    }
    
    logger.info(f"Event checks completed: {total_summary}")
    return total_summary
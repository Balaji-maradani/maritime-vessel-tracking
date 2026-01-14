"""
Management command to test vessel subscription and notification system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Vessel, VesselSubscription, Event
from core.services.notification_service import NotificationService

User = get_user_model()


class Command(BaseCommand):
    help = 'Test vessel subscription and notification system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test user and vessel subscription',
        )
        parser.add_argument(
            '--trigger-events',
            action='store_true',
            help='Trigger test events for subscribed vessels',
        )
        parser.add_argument(
            '--list-subscriptions',
            action='store_true',
            help='List all vessel subscriptions',
        )

    def handle(self, *args, **options):
        if options['create_test_data']:
            self._create_test_data()
        
        if options['list_subscriptions']:
            self._list_subscriptions()
        
        if options['trigger_events']:
            self._trigger_test_events()

    def _create_test_data(self):
        """Create test user and vessel subscription."""
        self.stdout.write('Creating test data...')
        
        # Create test user if doesn't exist
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'role': 'OPERATOR'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'✅ Created test user: {user.username}')
        else:
            self.stdout.write(f'✅ Using existing test user: {user.username}')
        
        # Get a vessel to subscribe to
        vessel = Vessel.objects.first()
        if not vessel:
            self.stdout.write(self.style.ERROR('❌ No vessels found. Run update_vessels command first.'))
            return
        
        # Create subscription
        subscription, created = VesselSubscription.objects.get_or_create(
            user=user,
            vessel=vessel,
            defaults={
                'subscription_type': 'ALL_EVENTS',
                'notify_storm_zones': True,
                'notify_piracy_zones': True,
                'notify_congestion': True,
                'notify_position_updates': False,
            }
        )
        
        if created:
            self.stdout.write(f'✅ Created subscription: {user.username} -> {vessel.name}')
        else:
            self.stdout.write(f'✅ Using existing subscription: {user.username} -> {vessel.name}')
        
        self.stdout.write(self.style.SUCCESS('Test data creation completed!'))

    def _list_subscriptions(self):
        """List all vessel subscriptions."""
        self.stdout.write('📋 Current Vessel Subscriptions:')
        
        subscriptions = VesselSubscription.objects.filter(is_active=True).select_related('user', 'vessel')
        
        if not subscriptions.exists():
            self.stdout.write('No active subscriptions found.')
            return
        
        for subscription in subscriptions:
            self.stdout.write(f'  👤 {subscription.user.username} -> 🚢 {subscription.vessel.name}')
            self.stdout.write(f'     Type: {subscription.subscription_type}')
            self.stdout.write(f'     Storm: {subscription.notify_storm_zones}, '
                            f'Piracy: {subscription.notify_piracy_zones}, '
                            f'Congestion: {subscription.notify_congestion}')
            self.stdout.write('---')

    def _trigger_test_events(self):
        """Trigger test events for subscribed vessels."""
        self.stdout.write('🚨 Triggering test events...')
        
        # Get subscribed vessels
        subscribed_vessels = Vessel.objects.filter(
            subscribers__is_active=True
        ).distinct()
        
        if not subscribed_vessels.exists():
            self.stdout.write(self.style.ERROR('❌ No subscribed vessels found. Create subscriptions first.'))
            return
        
        events_created = 0
        notifications_created = 0
        
        for vessel in subscribed_vessels[:3]:  # Test with first 3 vessels
            # Create storm zone entry event
            storm_event = Event.objects.create(
                vessel=vessel,
                event_type='STORM_ENTRY',
                location=f'Storm Zone near {vessel.last_position_lat}, {vessel.last_position_lon}',
                details=f'Vessel {vessel.name} entered severe weather area with wind speeds up to 75 knots'
            )
            events_created += 1
            
            # Trigger notifications
            storm_notifications = NotificationService.notify_users_for_event(storm_event)
            notifications_created += storm_notifications
            
            self.stdout.write(f'⛈️ Created storm event for {vessel.name} -> {storm_notifications} notifications')
            
            # Create piracy risk event
            piracy_event = Event.objects.create(
                vessel=vessel,
                event_type='PIRACY_RISK',
                location=f'High Risk Zone near {vessel.last_position_lat}, {vessel.last_position_lon}',
                details=f'Vessel {vessel.name} entered known piracy risk area - enhanced security recommended'
            )
            events_created += 1
            
            # Trigger notifications
            piracy_notifications = NotificationService.notify_users_for_event(piracy_event)
            notifications_created += piracy_notifications
            
            self.stdout.write(f'🏴‍☠️ Created piracy event for {vessel.name} -> {piracy_notifications} notifications')
            
            # Create congestion event
            congestion_event = Event.objects.create(
                vessel=vessel,
                event_type='HIGH_CONGESTION',
                location='Port of Dubai, UAE',
                details=f'Vessel {vessel.name} approaching high congestion port - expect delays'
            )
            events_created += 1
            
            # Trigger notifications
            congestion_notifications = NotificationService.notify_users_for_event(congestion_event)
            notifications_created += congestion_notifications
            
            self.stdout.write(f'🚢 Created congestion event for {vessel.name} -> {congestion_notifications} notifications')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Test events completed! Created {events_created} events and {notifications_created} notifications'
            )
        )
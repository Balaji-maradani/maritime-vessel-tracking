"""
Management command to test the voyage history and replay system.

This command tests:
1. Position recording and storage
2. Voyage association
3. Route reconstruction
4. Replay data generation
5. Audit logging
6. Data cleanup

Usage:
    python manage.py test_voyage_history
    python manage.py test_voyage_history --create-sample-data
    python manage.py test_voyage_history --test-replay
    python manage.py test_voyage_history --cleanup --dry-run
"""

import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from core.models import Vessel, Voyage, Port, VesselPosition, VoyageAuditLog
from core.services.voyage_history import VoyageHistoryService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test the voyage history and replay system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample voyage and position data for testing',
        )
        parser.add_argument(
            '--test-replay',
            action='store_true',
            help='Test voyage replay functionality',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Test data cleanup functionality',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform dry run without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        """
        Main command handler.
        """
        self.verbosity = 2 if options['verbose'] else 1
        
        self.stdout.write(
            self.style.SUCCESS('🚢 Starting Voyage History System Test')
        )
        
        try:
            service = VoyageHistoryService()
            
            # Test 1: Basic Position Recording
            self._test_position_recording(service)
            
            # Test 2: Voyage Association
            self._test_voyage_association(service)
            
            # Test 3: Create Sample Data (if requested)
            if options['create_sample_data']:
                self._create_sample_data(service)
            
            # Test 4: Route Reconstruction
            self._test_route_reconstruction(service)
            
            # Test 5: Replay Functionality (if requested)
            if options['test_replay']:
                self._test_replay_functionality(service)
            
            # Test 6: Statistics Generation
            self._test_statistics_generation(service)
            
            # Test 7: Audit Logging
            self._test_audit_logging()
            
            # Test 8: Data Cleanup (if requested)
            if options['cleanup']:
                self._test_data_cleanup(service, options['dry_run'])
            
            self.stdout.write(
                self.style.SUCCESS('✅ Voyage History System Test Completed Successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Test failed: {str(e)}')
            )
            if self.verbosity >= 2:
                import traceback
                self.stdout.write(traceback.format_exc())
            raise

    def _test_position_recording(self, service):
        """
        Test basic position recording functionality.
        """
        self.stdout.write('\n📍 Testing Position Recording...')
        
        try:
            # Get or create a test vessel
            vessel, created = Vessel.objects.get_or_create(
                imo_number='IMO9999999',
                defaults={
                    'name': 'Test Vessel History',
                    'vessel_type': 'Container Ship',
                    'flag': 'Test Flag',
                    'cargo_type': 'Containers',
                    'operator': 'Test Operator'
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Created test vessel: {vessel.name}')
            else:
                self.stdout.write(f'  ✓ Using existing vessel: {vessel.name}')
            
            # Record a test position
            test_timestamp = timezone.now()
            position = service.record_position(
                vessel=vessel,
                latitude=25.2048,
                longitude=55.2708,
                timestamp=test_timestamp,
                speed=12.5,
                heading=45,
                source='TEST',
                accuracy=10.0
            )
            
            self.stdout.write(f'  ✓ Recorded position: {position.latitude}, {position.longitude}')
            self.stdout.write(f'  📊 Position ID: {position.id}')
            
            # Test duplicate prevention
            duplicate_position = service.record_position(
                vessel=vessel,
                latitude=25.2048,
                longitude=55.2708,
                timestamp=test_timestamp,
                speed=13.0,  # Different speed
                heading=50,  # Different heading
                source='TEST'
            )
            
            if duplicate_position.id == position.id:
                self.stdout.write('  ✓ Duplicate position prevention working')
            else:
                self.stdout.write('  ⚠️  Duplicate position was created')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Position recording failed: {str(e)}'))

    def _test_voyage_association(self, service):
        """
        Test automatic voyage association.
        """
        self.stdout.write('\n🛳️  Testing Voyage Association...')
        
        try:
            # Get test vessel
            vessel = Vessel.objects.get(imo_number='IMO9999999')
            
            # Get or create test ports
            port_from, _ = Port.objects.get_or_create(
                name='Test Port A',
                defaults={
                    'location': 'Test Location A',
                    'country': 'Test Country',
                    'congestion_score': 5.0,
                    'avg_wait_time': 3.0,
                    'arrivals_count': 100,
                    'departures_count': 95
                }
            )
            
            port_to, _ = Port.objects.get_or_create(
                name='Test Port B',
                defaults={
                    'location': 'Test Location B',
                    'country': 'Test Country',
                    'congestion_score': 4.0,
                    'avg_wait_time': 2.5,
                    'arrivals_count': 80,
                    'departures_count': 85
                }
            )
            
            # Create a test voyage
            voyage = Voyage.objects.create(
                vessel=vessel,
                port_from=port_from,
                port_to=port_to,
                departure_time=timezone.now() - timedelta(hours=2),
                status='IN_PROGRESS'
            )
            
            self.stdout.write(f'  ✓ Created test voyage: {voyage.id}')
            
            # Record position that should be associated with this voyage
            position = service.record_position(
                vessel=vessel,
                latitude=25.5000,
                longitude=55.5000,
                timestamp=timezone.now() - timedelta(hours=1),
                speed=15.0,
                heading=90,
                source='TEST'
            )
            
            if position.voyage and position.voyage.id == voyage.id:
                self.stdout.write(f'  ✓ Position correctly associated with voyage {voyage.id}')
            else:
                self.stdout.write(f'  ⚠️  Position not associated with voyage (voyage: {position.voyage})')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Voyage association failed: {str(e)}'))

    def _create_sample_data(self, service):
        """
        Create comprehensive sample data for testing.
        """
        self.stdout.write('\n🏗️  Creating Sample Data...')
        
        try:
            vessel = Vessel.objects.get(imo_number='IMO9999999')
            
            # Find an active voyage
            voyage = Voyage.objects.filter(vessel=vessel, status='IN_PROGRESS').first()
            
            if not voyage:
                self.stdout.write('  ⚠️  No active voyage found for sample data')
                return
            
            # Create a realistic route with multiple positions
            base_time = voyage.departure_time
            positions_data = [
                {'lat': 25.2048, 'lon': 55.2708, 'speed': 0.0, 'heading': 0, 'hours_offset': 0},    # Port departure
                {'lat': 25.2500, 'lon': 55.3000, 'speed': 8.5, 'heading': 45, 'hours_offset': 0.5},  # Leaving port
                {'lat': 25.4000, 'lon': 55.5000, 'speed': 15.2, 'heading': 60, 'hours_offset': 2},   # Open water
                {'lat': 25.8000, 'lon': 56.0000, 'speed': 18.5, 'heading': 75, 'hours_offset': 6},   # Cruising
                {'lat': 26.2000, 'lon': 56.8000, 'speed': 16.8, 'heading': 80, 'hours_offset': 12},  # Mid voyage
                {'lat': 26.5000, 'lon': 57.5000, 'speed': 14.2, 'heading': 85, 'hours_offset': 18},  # Approaching
                {'lat': 26.7000, 'lon': 58.0000, 'speed': 8.0, 'heading': 90, 'hours_offset': 23},   # Slowing down
                {'lat': 26.8000, 'lon': 58.2000, 'speed': 2.5, 'heading': 95, 'hours_offset': 24},   # Port approach
            ]
            
            created_positions = 0
            for pos_data in positions_data:
                timestamp = base_time + timedelta(hours=pos_data['hours_offset'])
                
                position = service.record_position(
                    vessel=vessel,
                    latitude=pos_data['lat'],
                    longitude=pos_data['lon'],
                    timestamp=timestamp,
                    speed=pos_data['speed'],
                    heading=pos_data['heading'],
                    source='SAMPLE_DATA'
                )
                
                created_positions += 1
            
            self.stdout.write(f'  ✓ Created {created_positions} sample positions')
            self.stdout.write(f'  📊 Voyage duration: {positions_data[-1]["hours_offset"]} hours')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Sample data creation failed: {str(e)}'))

    def _test_route_reconstruction(self, service):
        """
        Test route reconstruction functionality.
        """
        self.stdout.write('\n🗺️  Testing Route Reconstruction...')
        
        try:
            # Find a voyage with positions
            voyage = Voyage.objects.filter(
                positions__isnull=False
            ).distinct().first()
            
            if not voyage:
                self.stdout.write('  ⚠️  No voyage with positions found')
                return
            
            # Get route data
            route_data = service.get_voyage_route(voyage, include_interpolated=False)
            
            self.stdout.write(f'  ✓ Retrieved route for voyage {voyage.id}')
            self.stdout.write(f'  📊 Route positions: {len(route_data)}')
            
            if route_data:
                first_pos = route_data[0]
                last_pos = route_data[-1]
                
                self.stdout.write(f'  📍 Start: {first_pos["latitude"]:.4f}, {first_pos["longitude"]:.4f}')
                self.stdout.write(f'  📍 End: {last_pos["latitude"]:.4f}, {last_pos["longitude"]:.4f}')
                
                # Test with interpolation
                route_with_interp = service.get_voyage_route(voyage, include_interpolated=True)
                self.stdout.write(f'  📊 With interpolation: {len(route_with_interp)} positions')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Route reconstruction failed: {str(e)}'))

    def _test_replay_functionality(self, service):
        """
        Test voyage replay data generation.
        """
        self.stdout.write('\n▶️  Testing Replay Functionality...')
        
        try:
            # Find a voyage with positions
            voyage = Voyage.objects.filter(
                positions__isnull=False
            ).distinct().first()
            
            if not voyage:
                self.stdout.write('  ⚠️  No voyage with positions found for replay')
                return
            
            # Generate replay data
            replay_data = service.generate_replay_data(
                voyage=voyage,
                speed_multiplier=2.0,
                interpolate_gaps=True
            )
            
            if 'error' in replay_data:
                self.stdout.write(f'  ❌ Replay generation failed: {replay_data["error"]}')
                return
            
            self.stdout.write(f'  ✓ Generated replay data for voyage {voyage.id}')
            
            metadata = replay_data.get('metadata', {})
            self.stdout.write(f'  📊 Total positions: {metadata.get("total_positions", 0)}')
            self.stdout.write(f'  ⏱️  Actual duration: {metadata.get("actual_duration_seconds", 0):.0f} seconds')
            self.stdout.write(f'  ⏱️  Replay duration: {metadata.get("replay_duration_seconds", 0):.0f} seconds')
            self.stdout.write(f'  📏 Total distance: {metadata.get("total_distance_nm", 0):.2f} nm')
            self.stdout.write(f'  🚢 Average speed: {metadata.get("average_speed", 0):.2f} knots')
            
            # Test different speed multipliers
            fast_replay = service.generate_replay_data(voyage, speed_multiplier=10.0)
            if 'metadata' in fast_replay:
                fast_duration = fast_replay['metadata'].get('replay_duration_seconds', 0)
                self.stdout.write(f'  ⚡ 10x speed replay duration: {fast_duration:.0f} seconds')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Replay functionality failed: {str(e)}'))

    def _test_statistics_generation(self, service):
        """
        Test voyage statistics generation.
        """
        self.stdout.write('\n📈 Testing Statistics Generation...')
        
        try:
            # Find a voyage with positions
            voyage = Voyage.objects.filter(
                positions__isnull=False
            ).distinct().first()
            
            if not voyage:
                self.stdout.write('  ⚠️  No voyage with positions found for statistics')
                return
            
            # Generate statistics
            stats = service.get_voyage_statistics(voyage)
            
            if 'error' in stats:
                self.stdout.write(f'  ❌ Statistics generation failed: {stats["error"]}')
                return
            
            self.stdout.write(f'  ✓ Generated statistics for voyage {voyage.id}')
            
            voyage_stats = stats.get('statistics', {})
            self.stdout.write(f'  📊 Total positions: {voyage_stats.get("total_positions", 0)}')
            self.stdout.write(f'  📏 Total distance: {voyage_stats.get("total_distance_nm", 0)} nm')
            self.stdout.write(f'  ⏱️  Duration: {voyage_stats.get("duration_hours", 0):.2f} hours')
            self.stdout.write(f'  🚢 Average speed: {voyage_stats.get("average_speed_knots", 0):.2f} knots')
            self.stdout.write(f'  🚢 Max speed: {voyage_stats.get("max_speed_knots", 0):.2f} knots')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Statistics generation failed: {str(e)}'))

    def _test_audit_logging(self):
        """
        Test audit logging functionality.
        """
        self.stdout.write('\n📋 Testing Audit Logging...')
        
        try:
            # Count recent audit logs
            recent_logs = VoyageAuditLog.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=1)
            ).count()
            
            self.stdout.write(f'  📊 Recent audit logs (1h): {recent_logs}')
            
            # Check different action types
            action_counts = {}
            for action, _ in VoyageAuditLog.ACTION_CHOICES:
                count = VoyageAuditLog.objects.filter(action=action).count()
                if count > 0:
                    action_counts[action] = count
            
            self.stdout.write('  📊 Audit log actions:')
            for action, count in action_counts.items():
                self.stdout.write(f'     {action}: {count}')
            
            # Test manual audit log creation
            vessel = Vessel.objects.first()
            if vessel:
                VoyageAuditLog.log_action(
                    vessel=vessel,
                    action='SYSTEM_UPDATE',
                    description='Test audit log entry from management command',
                    metadata={'test': True, 'command': 'test_voyage_history'},
                    compliance_category='TESTING'
                )
                self.stdout.write('  ✓ Created test audit log entry')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Audit logging test failed: {str(e)}'))

    def _test_data_cleanup(self, service, dry_run):
        """
        Test data cleanup functionality.
        """
        self.stdout.write('\n🧹 Testing Data Cleanup...')
        
        try:
            # Test position cleanup
            position_result = service.cleanup_old_positions(dry_run=dry_run)
            
            self.stdout.write(f'  📊 Position cleanup results:')
            self.stdout.write(f'     Dry run: {position_result.get("dry_run", False)}')
            self.stdout.write(f'     Records found: {position_result.get("records_found", 0)}')
            self.stdout.write(f'     Records deleted: {position_result.get("records_deleted", 0)}')
            self.stdout.write(f'     Retention days: {position_result.get("retention_days", 0)}')
            
            # Test audit log cleanup
            audit_result = service.cleanup_old_audit_logs(dry_run=dry_run)
            
            self.stdout.write(f'  📊 Audit log cleanup results:')
            self.stdout.write(f'     Dry run: {audit_result.get("dry_run", False)}')
            self.stdout.write(f'     Records found: {audit_result.get("records_found", 0)}')
            self.stdout.write(f'     Records deleted: {audit_result.get("records_deleted", 0)}')
            self.stdout.write(f'     Retention days: {audit_result.get("retention_days", 0)}')
            
            if dry_run:
                self.stdout.write('  ℹ️  This was a dry run - no data was actually deleted')
            else:
                self.stdout.write('  ✓ Cleanup completed')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Data cleanup test failed: {str(e)}'))

    def _log_verbose(self, message):
        """
        Log message only if verbose mode is enabled.
        """
        if self.verbosity >= 2:
            self.stdout.write(f'  🔍 {message}')
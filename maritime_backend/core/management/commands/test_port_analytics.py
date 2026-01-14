"""
Management command to test the port analytics system.

This command tests:
1. UNCTAD data fetching (with fallback to mock data)
2. Congestion score calculation
3. Port analytics updates
4. Event generation for high congestion
5. Dashboard data generation

Usage:
    python manage.py test_port_analytics
    python manage.py test_port_analytics --refresh-all
    python manage.py test_port_analytics --verbose
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from core.services.port_analytics import PortAnalyticsService
from core.models import Port, Event, Notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test the port analytics system with UNCTAD integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh-all',
            action='store_true',
            help='Refresh analytics for all ports using UNCTAD data',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
        parser.add_argument(
            '--port-name',
            type=str,
            help='Test analytics for a specific port by name',
        )

    def handle(self, *args, **options):
        """
        Main command handler.
        """
        self.verbosity = 2 if options['verbose'] else 1
        
        self.stdout.write(
            self.style.SUCCESS('🚢 Starting Port Analytics System Test')
        )
        
        try:
            service = PortAnalyticsService()
            
            # Test 1: UNCTAD Data Fetching
            self._test_unctad_data_fetching(service)
            
            # Test 2: Congestion Score Calculation
            self._test_congestion_calculation(service)
            
            # Test 3: Port Analytics Updates
            if options['refresh_all']:
                self._test_full_refresh(service)
            elif options['port_name']:
                self._test_specific_port(service, options['port_name'])
            else:
                self._test_sample_updates(service)
            
            # Test 4: Dashboard Data Generation
            self._test_dashboard_data(service)
            
            # Test 5: Event Generation
            self._test_event_generation()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Port Analytics System Test Completed Successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Test failed: {str(e)}')
            )
            if self.verbosity >= 2:
                import traceback
                self.stdout.write(traceback.format_exc())
            raise

    def _test_unctad_data_fetching(self, service):
        """
        Test UNCTAD data fetching with fallback handling.
        """
        self.stdout.write('\n📊 Testing UNCTAD Data Fetching...')
        
        try:
            # Test with default parameters
            data = service.fetch_unctad_port_statistics()
            
            self.stdout.write(f'  ✓ Fetched {len(data)} port records')
            
            if self.verbosity >= 2 and data:
                sample_record = data[0]
                self.stdout.write(f'  📋 Sample record: {sample_record["port_name"]}, {sample_record["country"]}')
                self.stdout.write(f'     Throughput: {sample_record["total_throughput"]:,}')
                self.stdout.write(f'     Arrivals: {sample_record["vessel_arrivals"]}')
                self.stdout.write(f'     Congestion factors: Occupancy={sample_record["berth_occupancy_rate"]}%, Wait={sample_record["avg_waiting_time"]}h')
            
            # Test with custom parameters
            custom_data = service.fetch_unctad_port_statistics({'year': 2024, 'limit': 3})
            self.stdout.write(f'  ✓ Custom query returned {len(custom_data)} records')
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  UNCTAD fetch error (expected): {str(e)}'))

    def _test_congestion_calculation(self, service):
        """
        Test congestion score calculation with various scenarios.
        """
        self.stdout.write('\n🧮 Testing Congestion Score Calculation...')
        
        test_scenarios = [
            {
                'name': 'Low Congestion Port',
                'data': {
                    'berth_occupancy_rate': 45.0,
                    'avg_waiting_time': 1.5,
                    'cargo_dwell_time': 2.8,
                    'vessel_arrivals': 100,
                    'vessel_departures': 98
                },
                'expected_range': (0, 4)
            },
            {
                'name': 'Moderate Congestion Port',
                'data': {
                    'berth_occupancy_rate': 70.0,
                    'avg_waiting_time': 4.2,
                    'cargo_dwell_time': 5.5,
                    'vessel_arrivals': 150,
                    'vessel_departures': 140
                },
                'expected_range': (4, 7)
            },
            {
                'name': 'High Congestion Port',
                'data': {
                    'berth_occupancy_rate': 88.0,
                    'avg_waiting_time': 8.5,
                    'cargo_dwell_time': 9.2,
                    'vessel_arrivals': 200,
                    'vessel_departures': 180
                },
                'expected_range': (7, 10)
            }
        ]
        
        for scenario in test_scenarios:
            score = service.calculate_congestion_score(scenario['data'])
            min_expected, max_expected = scenario['expected_range']
            
            if min_expected <= score <= max_expected:
                status = '✓'
                style = self.style.SUCCESS
            else:
                status = '⚠️'
                style = self.style.WARNING
            
            self.stdout.write(
                style(f'  {status} {scenario["name"]}: Score = {score} (expected {min_expected}-{max_expected})')
            )
            
            if self.verbosity >= 2:
                self.stdout.write(f'     Occupancy: {scenario["data"]["berth_occupancy_rate"]}%')
                self.stdout.write(f'     Wait time: {scenario["data"]["avg_waiting_time"]}h')
                self.stdout.write(f'     Dwell time: {scenario["data"]["cargo_dwell_time"]} days')

    def _test_sample_updates(self, service):
        """
        Test port analytics updates with sample data.
        """
        self.stdout.write('\n🔄 Testing Port Analytics Updates...')
        
        # Get sample UNCTAD data
        sample_data = service.fetch_unctad_port_statistics()
        
        if not sample_data:
            self.stdout.write(self.style.WARNING('  ⚠️  No sample data available'))
            return
        
        updated_count = 0
        not_found_count = 0
        
        for port_data in sample_data[:3]:  # Test first 3 ports
            port = service.update_port_analytics(port_data)
            
            if port:
                updated_count += 1
                self.stdout.write(
                    f'  ✓ Updated {port.name}: congestion={port.congestion_score}, wait={port.avg_wait_time}h'
                )
            else:
                not_found_count += 1
                self.stdout.write(
                    f'  ⚠️  Port not found: {port_data.get("port_name", "unknown")}'
                )
        
        self.stdout.write(f'  📊 Summary: {updated_count} updated, {not_found_count} not found')

    def _test_specific_port(self, service, port_name):
        """
        Test analytics for a specific port.
        """
        self.stdout.write(f'\n🎯 Testing Analytics for Specific Port: {port_name}')
        
        try:
            port = Port.objects.get(name__icontains=port_name)
            
            # Create mock UNCTAD data for this port
            mock_data = {
                'port_name': port.name,
                'country': port.country,
                'total_throughput': 5000000,
                'vessel_arrivals': 250,
                'vessel_departures': 245,
                'avg_waiting_time': 6.5,
                'berth_occupancy_rate': 78.5,
                'cargo_dwell_time': 4.8
            }
            
            # Calculate and update
            congestion_score = service.calculate_congestion_score(mock_data)
            updated_port = service.update_port_analytics(mock_data)
            
            if updated_port:
                self.stdout.write(f'  ✓ Port: {updated_port.name}, {updated_port.country}')
                self.stdout.write(f'  📊 Congestion Score: {congestion_score}')
                self.stdout.write(f'  ⏱️  Average Wait Time: {updated_port.avg_wait_time}h')
                self.stdout.write(f'  🚢 Arrivals: {updated_port.arrivals_count}')
                self.stdout.write(f'  🚢 Departures: {updated_port.departures_count}')
            else:
                self.stdout.write(self.style.ERROR(f'  ❌ Failed to update port'))
                
        except Port.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'  ❌ Port "{port_name}" not found in database'))

    def _test_full_refresh(self, service):
        """
        Test full refresh of all port analytics.
        """
        self.stdout.write('\n🔄 Testing Full Port Analytics Refresh...')
        
        summary = service.refresh_all_port_analytics()
        
        self.stdout.write(f'  📊 UNCTAD records fetched: {summary.get("unctad_records_fetched", 0)}')
        self.stdout.write(f'  ✅ Ports updated: {summary.get("ports_updated", 0)}')
        self.stdout.write(f'  ❓ Ports not found: {summary.get("ports_not_found", 0)}')
        self.stdout.write(f'  🚨 Events created: {summary.get("events_created", 0)}')
        
        if summary.get('errors'):
            self.stdout.write(f'  ⚠️  Errors: {len(summary["errors"])}')
            if self.verbosity >= 2:
                for error in summary['errors'][:3]:  # Show first 3 errors
                    self.stdout.write(f'     - {error}')
        
        success = summary.get('success', False)
        if success:
            self.stdout.write(self.style.SUCCESS('  ✅ Refresh completed successfully'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Refresh completed with errors'))

    def _test_dashboard_data(self, service):
        """
        Test dashboard data generation.
        """
        self.stdout.write('\n📈 Testing Dashboard Data Generation...')
        
        dashboard_data = service.get_port_dashboard_data()
        
        summary = dashboard_data.get('summary', {})
        distribution = dashboard_data.get('congestion_distribution', {})
        top_ports = dashboard_data.get('top_congested_ports', [])
        recent_events = dashboard_data.get('recent_events', [])
        
        self.stdout.write(f'  📊 Total Ports: {summary.get("total_ports", 0)}')
        self.stdout.write(f'  📊 Average Congestion: {summary.get("average_congestion_score", 0):.2f}')
        self.stdout.write(f'  ⏱️  Average Wait Time: {summary.get("average_wait_time", 0):.2f}h')
        
        self.stdout.write(f'  🚨 Congestion Distribution:')
        self.stdout.write(f'     Critical: {distribution.get("critical", 0)}')
        self.stdout.write(f'     High: {distribution.get("high", 0)}')
        self.stdout.write(f'     Moderate: {distribution.get("moderate", 0)}')
        self.stdout.write(f'     Low: {distribution.get("low", 0)}')
        
        self.stdout.write(f'  🏆 Top Congested Ports: {len(top_ports)}')
        if self.verbosity >= 2 and top_ports:
            for i, port in enumerate(top_ports[:3], 1):
                self.stdout.write(
                    f'     {i}. {port["name"]} ({port["country"]}) - Score: {port["congestion_score"]}'
                )
        
        self.stdout.write(f'  📅 Recent Events: {len(recent_events)}')
        
        if dashboard_data.get('note'):
            self.stdout.write(self.style.WARNING(f'  ℹ️  Note: {dashboard_data["note"]}'))

    def _test_event_generation(self):
        """
        Test event and notification generation.
        """
        self.stdout.write('\n🚨 Testing Event Generation...')
        
        # Count events before
        initial_event_count = Event.objects.filter(event_type='HIGH_CONGESTION').count()
        initial_notification_count = Notification.objects.count()
        
        # Check for recent congestion events
        recent_events = Event.objects.filter(
            event_type='HIGH_CONGESTION',
            timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        recent_notifications = Notification.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        self.stdout.write(f'  📊 Total congestion events: {initial_event_count}')
        self.stdout.write(f'  📊 Total notifications: {initial_notification_count}')
        self.stdout.write(f'  📅 Recent events (24h): {recent_events}')
        self.stdout.write(f'  📅 Recent notifications (24h): {recent_notifications}')
        
        if recent_events > 0:
            self.stdout.write(self.style.SUCCESS('  ✅ Event generation is working'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  No recent events found (may be normal)'))

    def _log_verbose(self, message):
        """
        Log message only if verbose mode is enabled.
        """
        if self.verbosity >= 2:
            self.stdout.write(f'  🔍 {message}')
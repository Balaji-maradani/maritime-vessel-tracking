"""
Management command to update vessel positions from AIS data.
"""

import json
from django.core.management.base import BaseCommand
from core.services.vessel_tracking import VesselTrackingService
from core.services.ais_data import AISDataService


class Command(BaseCommand):
    help = 'Update vessel positions from AIS data sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of vessels to fetch (default: 100)',
        )
        parser.add_argument(
            '--provider',
            type=str,
            choices=['marinetraffic', 'aishub', 'vesselfinder'],
            default='marinetraffic',
            help='AIS data provider to use (default: marinetraffic)',
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='API key for AIS provider (overrides settings)',
        )
        parser.add_argument(
            '--bbox',
            type=str,
            help='Bounding box filter: "min_lat,min_lon,max_lat,max_lon"',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test API connection without updating vessels',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        provider = options['provider']
        api_key = options['api_key']
        bbox_str = options['bbox']
        test_connection = options['test_connection']
        verbose = options['verbose']
        
        # Parse bounding box if provided
        bbox = None
        if bbox_str:
            try:
                coords = [float(x.strip()) for x in bbox_str.split(',')]
                if len(coords) != 4:
                    raise ValueError("Bounding box must have 4 coordinates")
                bbox = {
                    'min_lat': coords[0],
                    'min_lon': coords[1],
                    'max_lat': coords[2],
                    'max_lon': coords[3]
                }
            except ValueError as e:
                self.stdout.write(
                    self.style.ERROR(f'Invalid bounding box format: {e}')
                )
                return
        
        # Initialize services
        ais_service = AISDataService(api_key=api_key, provider=provider)
        tracking_service = VesselTrackingService(ais_service=ais_service)
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting vessel update using {provider} provider...')
        )
        
        # Test connection if requested
        if test_connection:
            self._test_connection(ais_service, verbose)
            return
        
        try:
            # Fetch and update vessels
            summary = tracking_service.fetch_and_update_vessels(limit=limit, bbox=bbox)
            
            # Display results
            self._display_summary(summary, verbose)
            
            if summary['success']:
                self.stdout.write(
                    self.style.SUCCESS('✅ Vessel update completed successfully!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Vessel update completed with some errors')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error updating vessels: {str(e)}')
            )
            raise
    
    def _test_connection(self, ais_service, verbose):
        """Test API connection and display results."""
        self.stdout.write('Testing API connection...')
        
        status = ais_service.validate_api_connection()
        
        if status['connection_status'] == 'connected':
            self.stdout.write(
                self.style.SUCCESS(f"✅ Connected to {status['provider']} API")
            )
            self.stdout.write(f"Test vessels fetched: {status['test_vessel_count']}")
        elif status['connection_status'] == 'no_api_key':
            self.stdout.write(
                self.style.WARNING(f"⚠️ No API key configured for {status['provider']}")
            )
            self.stdout.write("Will use mock data for testing")
        elif status['connection_status'] == 'no_data':
            self.stdout.write(
                self.style.WARNING(f"⚠️ Connected to {status['provider']} but no data returned")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Connection failed: {status.get('error', 'Unknown error')}")
            )
        
        if verbose:
            self.stdout.write("Connection details:")
            self.stdout.write(json.dumps(status, indent=2, default=str))
    
    def _display_summary(self, summary, verbose):
        """Display update summary."""
        self.stdout.write("\n📊 Update Summary:")
        self.stdout.write(f"  Fetched: {summary['fetched_count']} vessels")
        self.stdout.write(f"  Processed: {summary['processed_count']} vessels")
        self.stdout.write(f"  Created: {summary['created_count']} new vessels")
        self.stdout.write(f"  Updated: {summary['updated_count']} existing vessels")
        self.stdout.write(f"  Skipped: {summary['skipped_count']} vessels")
        self.stdout.write(f"  Errors: {summary['error_count']} vessels")
        
        if summary['errors'] and verbose:
            self.stdout.write("\n❌ Errors encountered:")
            for error in summary['errors'][:5]:  # Show first 5 errors
                self.stdout.write(f"  - {error}")
            if len(summary['errors']) > 5:
                self.stdout.write(f"  ... and {len(summary['errors']) - 5} more errors")
        
        if verbose:
            self.stdout.write("\nDetailed summary:")
            # Remove errors from verbose output to avoid duplication
            verbose_summary = {k: v for k, v in summary.items() if k != 'errors'}
            self.stdout.write(json.dumps(verbose_summary, indent=2, default=str))
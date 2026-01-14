"""
Management command to ensure fallback data exists in the database.
"""

from django.core.management.base import BaseCommand
from core.services.background_jobs import FallbackDataService
from core.models import Port, Vessel


class Command(BaseCommand):
    help = 'Ensure fallback data exists for ports and vessels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of fallback data even if data exists',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('Checking fallback data...')
        )
        
        # Check and create port data
        port_count = Port.objects.count()
        if port_count == 0 or force:
            if force and port_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'Force mode: Existing {port_count} ports will be supplemented')
                )
            
            FallbackDataService.ensure_minimum_port_data()
            new_port_count = Port.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Port data ensured: {new_port_count} ports available')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Port data OK: {port_count} ports already exist')
            )
        
        # Check and create vessel data
        vessel_count = Vessel.objects.count()
        if vessel_count == 0 or force:
            if force and vessel_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'Force mode: Existing {vessel_count} vessels will be supplemented')
                )
            
            FallbackDataService.ensure_minimum_vessel_data()
            new_vessel_count = Vessel.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Vessel data ensured: {new_vessel_count} vessels available')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Vessel data OK: {vessel_count} vessels already exist')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Fallback data check completed!')
        )
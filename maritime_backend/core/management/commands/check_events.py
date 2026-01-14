"""
Management command to run event checks and generate notifications.
"""

from django.core.management.base import BaseCommand
from core.services.notification_service import run_all_event_checks


class Command(BaseCommand):
    help = 'Run all event checks and generate notifications for high congestion, storms, and piracy risks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run checks without creating actual events and notifications',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting event checks...')
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No events or notifications will be created')
            )
            # In a real implementation, you'd modify the service to support dry-run mode
            return
        
        try:
            summary = run_all_event_checks()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Event checks completed successfully!\n"
                    f"Total events created: {summary['total_events_created']}\n"
                    f"Total notifications created: {summary['total_notifications_created']}\n"
                    f"Port congestion events: {summary['port_congestion']['events_created']}\n"
                    f"Storm zone events: {summary['storm_zones']['events_created']}\n"
                    f"Piracy zone events: {summary['piracy_zones']['events_created']}"
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running event checks: {str(e)}')
            )
            raise
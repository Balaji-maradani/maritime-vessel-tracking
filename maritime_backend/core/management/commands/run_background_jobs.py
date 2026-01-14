"""
Management command to run all background jobs for maritime analytics.
"""

import json
from django.core.management.base import BaseCommand
from core.services.background_jobs import BackgroundJobService


class Command(BaseCommand):
    help = 'Run all background jobs (port congestion, safety events, vessel positions)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job',
            type=str,
            choices=['all', 'ports', 'safety', 'vessels'],
            default='all',
            help='Specify which job to run (default: all)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        job_type = options['job']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting background job: {job_type}')
        )
        
        try:
            if job_type == 'all':
                summary = BackgroundJobService.run_all_background_jobs()
                self._display_all_jobs_summary(summary, verbose)
                
            elif job_type == 'ports':
                summary = BackgroundJobService.update_port_congestion()
                self._display_single_job_summary('Port Congestion Update', summary, verbose)
                
            elif job_type == 'safety':
                summary = BackgroundJobService.update_safety_events()
                self._display_single_job_summary('Safety Events Update', summary, verbose)
                
            elif job_type == 'vessels':
                summary = BackgroundJobService.update_vessel_positions()
                self._display_single_job_summary('Vessel Positions Update', summary, verbose)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running background job: {str(e)}')
            )
            raise
    
    def _display_all_jobs_summary(self, summary, verbose):
        """Display summary for all jobs."""
        success = summary.get('total_success', False)
        duration = summary.get('duration_seconds', 0)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ All background jobs completed successfully in {duration:.2f} seconds"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Some background jobs had issues (completed in {duration:.2f} seconds)"
                )
            )
        
        # Display individual job results
        jobs = summary.get('jobs', {})
        for job_name, job_result in jobs.items():
            job_success = job_result.get('success', False)
            status_icon = "✅" if job_success else "❌"
            
            self.stdout.write(f"  {status_icon} {job_name.replace('_', ' ').title()}")
            
            if verbose:
                if job_name == 'port_congestion':
                    ports_updated = job_result.get('ports_updated', 0)
                    ports_total = job_result.get('ports_total', 0)
                    self.stdout.write(f"    Updated {ports_updated}/{ports_total} ports")
                    
                elif job_name == 'vessel_positions':
                    vessels_updated = job_result.get('vessels_updated', 0)
                    vessels_total = job_result.get('vessels_total', 0)
                    self.stdout.write(f"    Updated {vessels_updated}/{vessels_total} vessels")
                    
                elif job_name == 'safety_events':
                    event_checks = job_result.get('event_checks', {})
                    total_events = event_checks.get('total_events_created', 0)
                    total_notifications = event_checks.get('total_notifications_created', 0)
                    self.stdout.write(f"    Created {total_events} events, {total_notifications} notifications")
                
                # Show errors if any
                errors = job_result.get('errors', [])
                if errors:
                    self.stdout.write(f"    Errors: {len(errors)}")
                    for error in errors[:3]:  # Show first 3 errors
                        self.stdout.write(f"      - {error}")
    
    def _display_single_job_summary(self, job_name, summary, verbose):
        """Display summary for a single job."""
        success = summary.get('success', False)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"✅ {job_name} completed successfully")
            )
        else:
            error = summary.get('error', 'Unknown error')
            self.stdout.write(
                self.style.ERROR(f"❌ {job_name} failed: {error}")
            )
            return
        
        if verbose:
            # Remove sensitive or overly verbose data for display
            display_summary = {k: v for k, v in summary.items() 
                             if k not in ['errors', 'event_checks', 'noaa_checks']}
            
            self.stdout.write("Detailed results:")
            self.stdout.write(json.dumps(display_summary, indent=2, default=str))
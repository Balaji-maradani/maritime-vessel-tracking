"""
Background job service for maritime analytics.

Handles periodic updates for:
- Port congestion data
- Safety events and weather alerts
- Vessel position updates
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from core.models import Port, Vessel, Event, Notification
from core.services.notification_service import run_all_event_checks
from core.services.safety import trigger_safety_events_from_noaa

logger = logging.getLogger(__name__)


class BackgroundJobService:
    """
    Service for managing background jobs and periodic updates.
    """
    
    @staticmethod
    def update_port_congestion() -> Dict[str, Any]:
        """
        Periodically update port congestion data using enhanced analytics service.
        Integrates UNCTAD-style port statistics and comprehensive congestion analysis.
        """
        logger.info("Starting enhanced port congestion update job...")
        
        try:
            # Try to use the enhanced analytics service first
            try:
                from core.services.port_analytics import PortAnalyticsService
                
                analytics_service = PortAnalyticsService()
                analytics_summary = analytics_service.refresh_all_port_analytics()
                
                # Transform analytics summary to match expected job format
                job_summary = {
                    'job': 'port_congestion_update',
                    'timestamp': timezone.now().isoformat(),
                    'method': 'enhanced_analytics',
                    'ports_total': analytics_summary.get('unctad_records_fetched', 0),
                    'ports_updated': analytics_summary.get('ports_updated', 0),
                    'ports_not_found': analytics_summary.get('ports_not_found', 0),
                    'events_created': analytics_summary.get('events_created', 0),
                    'errors_count': len(analytics_summary.get('errors', [])),
                    'errors': analytics_summary.get('errors', [])[:5],
                    'success': analytics_summary.get('success', False),
                    'analytics_summary': analytics_summary
                }
                
                logger.info(f"Enhanced port congestion update completed: {job_summary['ports_updated']} ports updated")
                return job_summary
                
            except ImportError:
                logger.warning("Enhanced analytics service not available, falling back to basic update")
                raise Exception("Analytics service not available")
                
        except Exception as analytics_error:
            logger.warning(f"Enhanced analytics failed: {str(analytics_error)}, using fallback method")
            
            # Fallback to basic congestion update
            try:
                ports_updated = 0
                errors = []
                
                # Get all ports
                ports = Port.objects.all()
                
                for port in ports:
                    try:
                        # Simulate fetching real-time congestion data
                        congestion_data = BackgroundJobService._fetch_port_congestion_data(port)
                        
                        # Update port with new data
                        port.congestion_score = congestion_data['congestion_score']
                        port.avg_wait_time = congestion_data['avg_wait_time']
                        port.arrivals_count = congestion_data['arrivals']
                        port.departures_count = congestion_data['departures']
                        port.last_updated = timezone.now()
                        port.save()
                        
                        ports_updated += 1
                        logger.debug(f"Updated congestion data for {port.name}")
                        
                    except Exception as e:
                        error_msg = f"Failed to update {port.name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg, exc_info=True)
                
                summary = {
                    'job': 'port_congestion_update',
                    'timestamp': timezone.now().isoformat(),
                    'method': 'fallback_basic',
                    'ports_total': ports.count(),
                    'ports_updated': ports_updated,
                    'errors_count': len(errors),
                    'errors': errors[:5],
                    'success': len(errors) == 0,
                    'fallback_reason': str(analytics_error)
                }
                
                logger.info(f"Fallback port congestion update completed: {ports_updated}/{ports.count()} ports updated")
                return summary
                
            except Exception as fallback_error:
                logger.error(f"Fallback port congestion update also failed: {str(fallback_error)}", exc_info=True)
                return {
                    'job': 'port_congestion_update',
                    'timestamp': timezone.now().isoformat(),
                    'method': 'failed',
                    'success': False,
                    'error': str(fallback_error),
                    'analytics_error': str(analytics_error)
                }
    
    @staticmethod
    def _fetch_port_congestion_data(port: Port) -> Dict[str, Any]:
        """
        Simulate fetching real-time port congestion data.
        In production, this would make actual API calls.
        """
        # Simulate API call with some realistic variation
        base_congestion = port.congestion_score if hasattr(port, 'congestion_score') else 5.0
        base_wait_time = port.avg_wait_time if hasattr(port, 'avg_wait_time') else 3.0
        
        # Add some realistic variation (±20%)
        congestion_variation = random.uniform(-0.2, 0.2)
        wait_time_variation = random.uniform(-0.2, 0.2)
        
        new_congestion = max(0.0, min(10.0, base_congestion + (base_congestion * congestion_variation)))
        new_wait_time = max(0.0, base_wait_time + (base_wait_time * wait_time_variation))
        
        # Simulate arrivals/departures based on congestion
        base_traffic = int(50 * (new_congestion / 10.0))  # Higher congestion = more traffic
        arrivals = base_traffic + random.randint(-10, 15)
        departures = base_traffic + random.randint(-15, 10)
        
        return {
            'congestion_score': round(new_congestion, 1),
            'avg_wait_time': round(new_wait_time, 1),
            'arrivals': max(0, arrivals),
            'departures': max(0, departures)
        }
    
    @staticmethod
    def update_safety_events() -> Dict[str, Any]:
        """
        Periodically check for safety events and update alerts.
        """
        logger.info("Starting safety events update job...")
        
        try:
            # Run the existing safety event checks
            safety_summary = run_all_event_checks()
            
            # Also trigger NOAA weather alerts if configured
            noaa_summary = {}
            try:
                noaa_summary = trigger_safety_events_from_noaa()
                logger.info(f"NOAA safety check completed: {noaa_summary}")
            except Exception as e:
                logger.warning(f"NOAA safety check failed: {str(e)}")
                noaa_summary = {'error': str(e)}
            
            summary = {
                'job': 'safety_events_update',
                'timestamp': timezone.now().isoformat(),
                'event_checks': safety_summary,
                'noaa_checks': noaa_summary,
                'success': True
            }
            
            logger.info("Safety events update completed successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Critical error in safety events update: {str(e)}", exc_info=True)
            return {
                'job': 'safety_events_update',
                'timestamp': timezone.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_vessel_positions() -> Dict[str, Any]:
        """
        Periodically update vessel positions from AIS data using enhanced tracking service.
        """
        logger.info("Starting vessel positions update job...")
        
        try:
            from core.services.vessel_tracking import VesselTrackingService
            
            # Initialize enhanced vessel tracking service
            tracking_service = VesselTrackingService()
            
            # Fetch and update vessels
            summary = tracking_service.fetch_and_update_vessels(limit=200)
            
            # Transform summary to match expected format
            job_summary = {
                'job': 'vessel_positions_update',
                'timestamp': timezone.now().isoformat(),
                'vessels_total': summary['fetched_count'],
                'vessels_updated': summary['updated_count'],
                'vessels_created': summary['created_count'],
                'vessels_skipped': summary['skipped_count'],
                'errors_count': summary['error_count'],
                'errors': summary['errors'][:5],  # Limit error details
                'success': summary['success']
            }
            
            logger.info(f"Vessel positions update completed: {summary['processed_count']} processed, "
                       f"{summary['created_count']} created, {summary['updated_count']} updated")
            return job_summary
            
        except Exception as e:
            logger.error(f"Critical error in vessel positions update: {str(e)}", exc_info=True)
            return {
                'job': 'vessel_positions_update',
                'timestamp': timezone.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def run_all_background_jobs() -> Dict[str, Any]:
        """
        Run all background jobs in sequence.
        """
        logger.info("Starting all background jobs...")
        start_time = timezone.now()
        
        jobs_summary = {
            'started_at': start_time.isoformat(),
            'jobs': {},
            'total_success': True
        }
        
        # Run port congestion update
        try:
            port_result = BackgroundJobService.update_port_congestion()
            jobs_summary['jobs']['port_congestion'] = port_result
            if not port_result.get('success', False):
                jobs_summary['total_success'] = False
        except Exception as e:
            logger.error(f"Port congestion job failed: {str(e)}", exc_info=True)
            jobs_summary['jobs']['port_congestion'] = {'success': False, 'error': str(e)}
            jobs_summary['total_success'] = False
        
        # Run safety events update
        try:
            safety_result = BackgroundJobService.update_safety_events()
            jobs_summary['jobs']['safety_events'] = safety_result
            if not safety_result.get('success', False):
                jobs_summary['total_success'] = False
        except Exception as e:
            logger.error(f"Safety events job failed: {str(e)}", exc_info=True)
            jobs_summary['jobs']['safety_events'] = {'success': False, 'error': str(e)}
            jobs_summary['total_success'] = False
        
        # Run vessel positions update
        try:
            vessel_result = BackgroundJobService.update_vessel_positions()
            jobs_summary['jobs']['vessel_positions'] = vessel_result
            if not vessel_result.get('success', False):
                jobs_summary['total_success'] = False
        except Exception as e:
            logger.error(f"Vessel positions job failed: {str(e)}", exc_info=True)
            jobs_summary['jobs']['vessel_positions'] = {'success': False, 'error': str(e)}
            jobs_summary['total_success'] = False
        
        end_time = timezone.now()
        jobs_summary['completed_at'] = end_time.isoformat()
        jobs_summary['duration_seconds'] = (end_time - start_time).total_seconds()
        
        logger.info(f"All background jobs completed in {jobs_summary['duration_seconds']:.2f} seconds")
        return jobs_summary


class FallbackDataService:
    """
    Service for providing fallback data when external APIs fail.
    """
    
    @staticmethod
    def get_fallback_port_data() -> List[Dict[str, Any]]:
        """
        Return fallback port congestion data when API fails.
        """
        return [
            {
                'name': 'Port of Dubai',
                'country': 'UAE',
                'congestion_score': 6.5,
                'avg_wait_time': 3.2,
                'arrivals': 42,
                'departures': 38
            },
            {
                'name': 'Port of Singapore',
                'country': 'Singapore',
                'congestion_score': 8.1,
                'avg_wait_time': 5.7,
                'arrivals': 67,
                'departures': 63
            },
            {
                'name': 'Port of Rotterdam',
                'country': 'Netherlands',
                'congestion_score': 4.8,
                'avg_wait_time': 2.1,
                'arrivals': 34,
                'departures': 41
            },
            {
                'name': 'Port of Shanghai',
                'country': 'China',
                'congestion_score': 9.2,
                'avg_wait_time': 7.8,
                'arrivals': 89,
                'departures': 82
            },
            {
                'name': 'Port of Los Angeles',
                'country': 'USA',
                'congestion_score': 7.3,
                'avg_wait_time': 4.5,
                'arrivals': 56,
                'departures': 52
            }
        ]
    
    @staticmethod
    def get_fallback_vessel_data() -> List[Dict[str, Any]]:
        """
        Return fallback vessel data when AIS API fails.
        """
        return [
            {
                'imo': 'IMO9234567',
                'mmsi': '123456789',
                'name': 'Ocean Explorer',
                'vessel_type': 'Container Ship',
                'flag': 'Panama',
                'latitude': 25.2048,
                'longitude': 55.2708,
                'speed': 12.5,
                'heading': 45,
                'timestamp': timezone.now().isoformat()
            },
            {
                'imo': 'IMO9876543',
                'mmsi': '234567890',
                'name': 'Maritime Pioneer',
                'vessel_type': 'Bulk Carrier',
                'flag': 'Liberia',
                'latitude': 26.0667,
                'longitude': 50.5577,
                'speed': 8.2,
                'heading': 180,
                'timestamp': timezone.now().isoformat()
            },
            {
                'imo': 'IMO9345678',
                'mmsi': '345678901',
                'name': 'Gulf Trader',
                'vessel_type': 'Tanker',
                'flag': 'Marshall Islands',
                'latitude': 24.4539,
                'longitude': 54.3773,
                'speed': 15.1,
                'heading': 270,
                'timestamp': timezone.now().isoformat()
            }
        ]
    
    @staticmethod
    def ensure_minimum_port_data():
        """
        Ensure there's always some port data available in the database.
        """
        if Port.objects.count() == 0:
            logger.info("No port data found, creating fallback data...")
            
            fallback_ports = FallbackDataService.get_fallback_port_data()
            
            for port_data in fallback_ports:
                Port.objects.get_or_create(
                    name=port_data['name'],
                    defaults={
                        'location': f"{port_data['name']} Port Area",
                        'country': port_data['country'],
                        'congestion_score': port_data['congestion_score'],
                        'avg_wait_time': port_data['avg_wait_time'],
                        'arrivals_count': port_data['arrivals'],
                        'departures_count': port_data['departures'],
                        'last_updated': timezone.now(),  # Use the correct field name
                    }
                )
            
            logger.info(f"Created {len(fallback_ports)} fallback ports")
    
    @staticmethod
    def ensure_minimum_vessel_data():
        """
        Ensure there's always some vessel data available in the database.
        """
        if Vessel.objects.count() == 0:
            logger.info("No vessel data found, creating fallback data...")
            
            fallback_vessels = FallbackDataService.get_fallback_vessel_data()
            
            for vessel_data in fallback_vessels:
                Vessel.objects.get_or_create(
                    imo_number=vessel_data['imo'],
                    defaults={
                        'mmsi': vessel_data['mmsi'],
                        'name': vessel_data['name'],
                        'vessel_type': vessel_data['vessel_type'],
                        'flag': vessel_data['flag'],
                        'cargo_type': 'General',
                        'operator': 'Unknown Operator',
                        'last_position_lat': vessel_data['latitude'],
                        'last_position_lon': vessel_data['longitude'],
                        'speed': vessel_data['speed'],
                        'heading': vessel_data['heading'],
                    }
                )
            
            logger.info(f"Created {len(fallback_vessels)} fallback vessels")
"""
Enhanced Vessel Tracking Service for processing and persisting AIS data.
Handles real-time vessel position updates with robust error handling and deduplication.
"""
import logging
from typing import Iterable, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError

from core.models import Vessel
from core.services.ais_data import AISDataService

logger = logging.getLogger(__name__)


class VesselTrackingService:
    """
    Enhanced service for processing and persisting vessel tracking data.
    """
    
    def __init__(self, ais_service: AISDataService = None):
        """
        Initialize vessel tracking service.
        
        Args:
            ais_service: AIS data service instance (optional)
        """
        self.ais_service = ais_service or AISDataService()
        self.update_threshold_minutes = getattr(settings, 'VESSEL_UPDATE_THRESHOLD_MINUTES', 5)
    
    def fetch_and_update_vessels(self, limit: int = 100, bbox: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Fetch vessel data from AIS service and update database records.
        
        Args:
            limit: Maximum number of vessels to fetch
            bbox: Optional bounding box filter
            
        Returns:
            Summary dictionary with processing statistics
        """
        logger.info(f"Starting vessel data fetch and update (limit: {limit})")
        
        summary = {
            'started_at': timezone.now().isoformat(),
            'fetched_count': 0,
            'processed_count': 0,
            'created_count': 0,
            'updated_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'errors': [],
            'success': False
        }
        
        try:
            # Fetch vessel data from AIS service
            vessel_data = self.ais_service.get_live_vessel_positions(limit=limit, bbox=bbox)
            summary['fetched_count'] = len(vessel_data)
            
            if not vessel_data:
                logger.warning("No vessel data received from AIS service")
                summary['success'] = True  # Not an error, just no data
                return summary
            
            # Process each vessel record
            for vessel_record in vessel_data:
                try:
                    result = self.process_vessel_record(vessel_record)
                    summary['processed_count'] += 1
                    
                    if result['action'] == 'created':
                        summary['created_count'] += 1
                    elif result['action'] == 'updated':
                        summary['updated_count'] += 1
                    elif result['action'] == 'skipped':
                        summary['skipped_count'] += 1
                        
                except Exception as e:
                    summary['error_count'] += 1
                    error_msg = f"Error processing vessel {vessel_record.get('imo', 'unknown')}: {str(e)}"
                    summary['errors'].append(error_msg)
                    logger.error(error_msg, exc_info=True)
            
            summary['success'] = summary['error_count'] == 0
            summary['completed_at'] = timezone.now().isoformat()
            
            logger.info(f"Vessel update completed: {summary['processed_count']} processed, "
                       f"{summary['created_count']} created, {summary['updated_count']} updated, "
                       f"{summary['error_count']} errors")
            
        except Exception as e:
            summary['error_count'] += 1
            summary['errors'].append(f"Critical error in vessel fetch: {str(e)}")
            logger.error(f"Critical error in fetch_and_update_vessels: {str(e)}", exc_info=True)
        
        return summary
    
    def process_vessel_record(self, vessel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single vessel record and update/create database entry.
        
        Args:
            vessel_data: Normalized vessel data from AIS service
            
        Returns:
            Dictionary with processing result
        """
        imo = vessel_data.get('imo', '').strip()
        mmsi = vessel_data.get('mmsi', '').strip()
        
        # Validate required fields
        if not imo and not mmsi:
            raise ValidationError("Vessel record missing both IMO and MMSI")
        
        # Normalize and validate vessel data
        normalized_data = self._normalize_vessel_data(vessel_data)
        
        # Check if we should update based on timestamp
        if not self._should_update_vessel(normalized_data):
            return {'action': 'skipped', 'reason': 'recent_update'}
        
        try:
            with transaction.atomic():
                vessel, created = self._upsert_vessel(normalized_data)
                
                action = 'created' if created else 'updated'
                logger.debug(f"Vessel {vessel.name} ({vessel.imo_number}) {action}")
                
                return {
                    'action': action,
                    'vessel_id': vessel.id,
                    'vessel_name': vessel.name,
                    'imo': vessel.imo_number
                }
                
        except IntegrityError as e:
            logger.error(f"Database integrity error for vessel {imo}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing vessel {imo}: {str(e)}")
            raise
    
    def _normalize_vessel_data(self, vessel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and validate vessel data fields.
        
        Args:
            vessel_data: Raw vessel data from AIS service
            
        Returns:
            Normalized vessel data dictionary
        """
        # Extract and clean basic fields
        imo = str(vessel_data.get('imo', '')).strip()
        mmsi = str(vessel_data.get('mmsi', '')).strip()
        name = str(vessel_data.get('name', 'Unknown Vessel')).strip()
        vessel_type = str(vessel_data.get('vessel_type', 'Unknown')).strip()
        flag = str(vessel_data.get('flag', 'Unknown')).strip()
        
        # Handle position data
        try:
            latitude = float(vessel_data.get('latitude', 0))
            longitude = float(vessel_data.get('longitude', 0))
            
            # Validate coordinate ranges
            if not (-90 <= latitude <= 90):
                logger.warning(f"Invalid latitude {latitude} for vessel {imo}")
                latitude = None
            if not (-180 <= longitude <= 180):
                logger.warning(f"Invalid longitude {longitude} for vessel {imo}")
                longitude = None
                
        except (ValueError, TypeError):
            latitude = longitude = None
        
        # Handle speed and heading
        try:
            speed = float(vessel_data.get('speed', 0))
            speed = max(0, min(speed, 100))  # Reasonable speed limits
        except (ValueError, TypeError):
            speed = None
        
        try:
            heading = int(vessel_data.get('heading', 0))
            heading = heading % 360  # Normalize to 0-359
        except (ValueError, TypeError):
            heading = None
        
        # Parse timestamp
        timestamp_str = vessel_data.get('timestamp')
        if timestamp_str:
            try:
                if isinstance(timestamp_str, str):
                    # Handle ISO format timestamp
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = timestamp_str
            except (ValueError, TypeError):
                timestamp = timezone.now()
        else:
            timestamp = timezone.now()
        
        return {
            'imo_number': imo,
            'mmsi': mmsi,
            'name': name,
            'vessel_type': vessel_type,
            'flag': flag,
            'cargo_type': str(vessel_data.get('cargo_type', 'Unknown')).strip(),
            'operator': str(vessel_data.get('operator', 'Unknown')).strip(),
            'last_position_lat': latitude,
            'last_position_lon': longitude,
            'speed': speed,
            'heading': heading,
            'position_timestamp': timestamp,
        }
    
    def _should_update_vessel(self, vessel_data: Dict[str, Any]) -> bool:
        """
        Determine if vessel should be updated based on timestamp and update threshold.
        
        Args:
            vessel_data: Normalized vessel data
            
        Returns:
            True if vessel should be updated
        """
        imo = vessel_data.get('imo_number')
        if not imo:
            return True  # Always process if no IMO to check against
        
        try:
            existing_vessel = Vessel.objects.get(imo_number=imo)
            
            # Check if enough time has passed since last update
            threshold = timezone.now() - timedelta(minutes=self.update_threshold_minutes)
            if existing_vessel.last_update > threshold:
                logger.debug(f"Skipping vessel {imo} - updated recently")
                return False
                
        except Vessel.DoesNotExist:
            # New vessel, always process
            return True
        
        return True
    
    def _upsert_vessel(self, vessel_data: Dict[str, Any]) -> Tuple[Vessel, bool]:
        """
        Create or update vessel record in database with voyage history integration.
        
        Args:
            vessel_data: Normalized vessel data
            
        Returns:
            Tuple of (vessel_instance, created_flag)
        """
        imo = vessel_data.get('imo_number')
        mmsi = vessel_data.get('mmsi')
        
        # Extract position timestamp for history recording
        position_timestamp = vessel_data.pop('position_timestamp', None)
        
        # Try to find existing vessel by IMO first, then MMSI
        existing_vessel = None
        if imo:
            try:
                existing_vessel = Vessel.objects.get(imo_number=imo)
            except Vessel.DoesNotExist:
                pass
        
        if not existing_vessel and mmsi:
            try:
                existing_vessel = Vessel.objects.get(mmsi=mmsi)
            except Vessel.DoesNotExist:
                pass
        
        if existing_vessel:
            # Update existing vessel
            for field, value in vessel_data.items():
                if value is not None:  # Only update non-null values
                    setattr(existing_vessel, field, value)
            
            existing_vessel.save()
            created = False
        else:
            # Create new vessel
            # Ensure we have either IMO or MMSI for unique identification
            if not imo and not mmsi:
                raise ValidationError("Cannot create vessel without IMO or MMSI")
            
            existing_vessel = Vessel.objects.create(**vessel_data)
            created = True
        
        # Record position in voyage history if we have location data
        if (vessel_data.get('last_position_lat') and 
            vessel_data.get('last_position_lon') and 
            position_timestamp):
            
            try:
                from core.services.voyage_history import VoyageHistoryService
                
                history_service = VoyageHistoryService()
                
                # Record position in history
                history_service.record_position(
                    vessel=existing_vessel,
                    latitude=vessel_data['last_position_lat'],
                    longitude=vessel_data['last_position_lon'],
                    timestamp=position_timestamp,
                    speed=vessel_data.get('speed'),
                    heading=vessel_data.get('heading'),
                    source='AIS'
                )
                
            except Exception as history_error:
                # Don't fail the main operation if history recording fails
                logger.warning(f"Failed to record position history for {existing_vessel.name}: {str(history_error)}")
        
        return existing_vessel, created
    
    def get_vessel_by_identifier(self, imo: str = None, mmsi: str = None) -> Optional[Vessel]:
        """
        Get vessel by IMO or MMSI.
        
        Args:
            imo: IMO number
            mmsi: MMSI number
            
        Returns:
            Vessel instance or None
        """
        if imo:
            try:
                return Vessel.objects.get(imo_number=imo)
            except Vessel.DoesNotExist:
                pass
        
        if mmsi:
            try:
                return Vessel.objects.get(mmsi=mmsi)
            except Vessel.DoesNotExist:
                pass
        
        return None
    
    def update_vessel_from_ais(self, imo: str) -> Dict[str, Any]:
        """
        Update a specific vessel from AIS data.
        
        Args:
            imo: IMO number of vessel to update
            
        Returns:
            Update result dictionary
        """
        try:
            vessel_data = self.ais_service.get_vessel_by_imo(imo)
            if not vessel_data:
                return {'success': False, 'error': 'Vessel not found in AIS data'}
            
            result = self.process_vessel_record(vessel_data)
            result['success'] = True
            return result
            
        except Exception as e:
            logger.error(f"Error updating vessel {imo} from AIS: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_stale_vessels(self, hours: int = 24) -> Iterable[Vessel]:
        """
        Get vessels that haven't been updated recently.
        
        Args:
            hours: Number of hours to consider as stale
            
        Returns:
            QuerySet of stale vessels
        """
        threshold = timezone.now() - timedelta(hours=hours)
        return Vessel.objects.filter(last_update__lt=threshold)
    
    def cleanup_old_positions(self, days: int = 30) -> int:
        """
        Clean up old vessel position data (if implemented with position history).
        
        Args:
            days: Number of days of history to keep
            
        Returns:
            Number of records cleaned up
        """
        # This would be implemented if we had a separate VesselPosition model
        # for historical tracking. For now, we only keep current positions.
        logger.info("Position cleanup not implemented - only current positions stored")
        return 0
    
    def validate_ais_connection(self) -> Dict[str, Any]:
        """
        Validate AIS service connection.
        
        Returns:
            Connection status dictionary
        """
        return self.ais_service.validate_api_connection()


# Legacy functions for backward compatibility
def _get_aishub_config() -> Tuple[str, str]:
    """Legacy function - use VesselTrackingService instead."""
    logger.warning("Using deprecated _get_aishub_config function")
    api_url = getattr(settings, "AISHUB_API_URL", "https://example-ais-hub.com/api/vessels")
    api_key = getattr(settings, "AISHUB_API_KEY", None)
    return api_url, api_key


def fetch_live_vessel_data(params: Dict[str, Any] = None) -> Iterable[Dict[str, Any]]:
    """Legacy function - use VesselTrackingService instead."""
    logger.warning("Using deprecated fetch_live_vessel_data function")
    service = VesselTrackingService()
    return service.ais_service.get_live_vessel_positions()


def upsert_vessel_from_ais_record(record: Dict[str, Any]) -> Optional[Vessel]:
    """Legacy function - use VesselTrackingService instead."""
    logger.warning("Using deprecated upsert_vessel_from_ais_record function")
    service = VesselTrackingService()
    try:
        result = service.process_vessel_record(record)
        return service.get_vessel_by_identifier(imo=record.get('imo'))
    except Exception as e:
        logger.error(f"Error in legacy upsert function: {str(e)}")
        return None


def refresh_vessel_positions(params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Legacy function - use VesselTrackingService instead."""
    logger.warning("Using deprecated refresh_vessel_positions function")
    service = VesselTrackingService()
    return service.fetch_and_update_vessels()



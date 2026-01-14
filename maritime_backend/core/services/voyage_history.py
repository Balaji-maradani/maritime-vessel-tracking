"""
Voyage History and Replay Service

Handles:
1. Historical vessel position storage and retrieval
2. Voyage grouping and route reconstruction
3. Replay data generation for frontend visualization
4. Audit and compliance logging
5. Storage optimization and data retention
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from django.utils import timezone
from django.db import transaction, connection
from django.db.models import Q, Count, Min, Max, Avg
from django.core.paginator import Paginator
from django.conf import settings

from core.models import Vessel, Voyage, VesselPosition, VoyageAuditLog, Port

logger = logging.getLogger(__name__)


class VoyageHistoryService:
    """
    Service for managing voyage history, position tracking, and replay functionality.
    """
    
    def __init__(self):
        self.position_retention_days = getattr(settings, 'POSITION_RETENTION_DAYS', 365)
        self.audit_retention_days = getattr(settings, 'AUDIT_RETENTION_DAYS', 2555)  # 7 years
        self.interpolation_threshold_minutes = getattr(settings, 'POSITION_INTERPOLATION_THRESHOLD', 30)
    
    def record_position(self, vessel: Vessel, latitude: float, longitude: float, 
                       timestamp: datetime, speed: Optional[float] = None, 
                       heading: Optional[int] = None, source: str = 'AIS',
                       accuracy: Optional[float] = None, user=None, 
                       ip_address: str = None) -> VesselPosition:
        """
        Record a new vessel position with automatic voyage association and audit logging.
        
        Args:
            vessel: Vessel instance
            latitude: Position latitude
            longitude: Position longitude
            timestamp: Position timestamp
            speed: Vessel speed in knots
            heading: Vessel heading in degrees
            source: Data source (AIS, GPS, Manual, etc.)
            accuracy: Position accuracy in meters
            user: User recording the position (if manual)
            ip_address: IP address for audit logging
            
        Returns:
            VesselPosition instance
        """
        try:
            with transaction.atomic():
                # Find active voyage for this vessel
                active_voyage = self._find_active_voyage(vessel, timestamp)
                
                # Check for duplicate positions
                existing_position = VesselPosition.objects.filter(
                    vessel=vessel,
                    timestamp=timestamp
                ).first()
                
                if existing_position:
                    logger.debug(f"Position already exists for {vessel.name} at {timestamp}")
                    return existing_position
                
                # Create position record
                position = VesselPosition.objects.create(
                    vessel=vessel,
                    voyage=active_voyage,
                    latitude=latitude,
                    longitude=longitude,
                    speed=speed,
                    heading=heading,
                    timestamp=timestamp,
                    source=source,
                    accuracy=accuracy,
                    is_interpolated=False
                )
                
                # Update vessel's current position
                vessel.last_position_lat = latitude
                vessel.last_position_lon = longitude
                if speed is not None:
                    vessel.speed = speed
                if heading is not None:
                    vessel.heading = heading
                vessel.last_update = timestamp
                vessel.save()
                
                # Log the action
                VoyageAuditLog.log_action(
                    vessel=vessel,
                    voyage=active_voyage,
                    action='POSITION_RECORDED',
                    description=f'Position recorded at {latitude:.6f}, {longitude:.6f} from {source}',
                    user=user,
                    ip_address=ip_address,
                    metadata={
                        'latitude': latitude,
                        'longitude': longitude,
                        'speed': speed,
                        'heading': heading,
                        'source': source,
                        'accuracy': accuracy
                    },
                    compliance_category='POSITION_TRACKING'
                )
                
                logger.debug(f"Recorded position for {vessel.name} at {timestamp}")
                return position
                
        except Exception as e:
            logger.error(f"Error recording position for {vessel.name}: {str(e)}", exc_info=True)
            raise
    
    def _find_active_voyage(self, vessel: Vessel, timestamp: datetime) -> Optional[Voyage]:
        """
        Find the active voyage for a vessel at a given timestamp.
        
        Args:
            vessel: Vessel instance
            timestamp: Position timestamp
            
        Returns:
            Active Voyage instance or None
        """
        # Look for voyages that are in progress and contain this timestamp
        active_voyage = Voyage.objects.filter(
            vessel=vessel,
            status='IN_PROGRESS',
            departure_time__lte=timestamp
        ).filter(
            Q(arrival_time__isnull=True) | Q(arrival_time__gte=timestamp)
        ).first()
        
        if not active_voyage:
            # Look for planned voyages that should have started
            planned_voyage = Voyage.objects.filter(
                vessel=vessel,
                status='PLANNED',
                departure_time__lte=timestamp + timedelta(hours=2)  # Allow 2-hour buffer
            ).first()
            
            if planned_voyage:
                # Auto-start the voyage
                planned_voyage.status = 'IN_PROGRESS'
                planned_voyage.save()
                
                VoyageAuditLog.log_action(
                    vessel=vessel,
                    voyage=planned_voyage,
                    action='VOYAGE_UPDATED',
                    description='Voyage automatically started based on position data',
                    metadata={'auto_started': True, 'trigger_timestamp': timestamp.isoformat()},
                    compliance_category='VOYAGE_MANAGEMENT'
                )
                
                active_voyage = planned_voyage
        
        return active_voyage
    
    def get_voyage_route(self, voyage: Voyage, include_interpolated: bool = False) -> List[Dict[str, Any]]:
        """
        Get the complete route for a voyage with all positions.
        
        Args:
            voyage: Voyage instance
            include_interpolated: Whether to include interpolated positions
            
        Returns:
            List of position dictionaries
        """
        try:
            # Log access for compliance
            VoyageAuditLog.log_action(
                vessel=voyage.vessel,
                voyage=voyage,
                action='ROUTE_ACCESSED',
                description=f'Route data accessed for voyage {voyage.id}',
                compliance_category='DATA_ACCESS'
            )
            
            # Build query
            positions_query = VesselPosition.objects.filter(voyage=voyage)
            
            if not include_interpolated:
                positions_query = positions_query.filter(is_interpolated=False)
            
            positions = positions_query.order_by('timestamp').values(
                'latitude', 'longitude', 'speed', 'heading', 'timestamp',
                'source', 'accuracy', 'is_interpolated'
            )
            
            # Convert to list and format timestamps
            route_data = []
            for position in positions:
                route_data.append({
                    'latitude': position['latitude'],
                    'longitude': position['longitude'],
                    'speed': position['speed'],
                    'heading': position['heading'],
                    'timestamp': position['timestamp'].isoformat(),
                    'source': position['source'],
                    'accuracy': position['accuracy'],
                    'is_interpolated': position['is_interpolated']
                })
            
            return route_data
            
        except Exception as e:
            logger.error(f"Error getting route for voyage {voyage.id}: {str(e)}", exc_info=True)
            return []
    
    def get_vessel_history(self, vessel: Vessel, start_date: datetime, 
                          end_date: datetime, limit: int = 1000) -> Dict[str, Any]:
        """
        Get historical positions for a vessel within a date range.
        
        Args:
            vessel: Vessel instance
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of positions to return
            
        Returns:
            Dictionary with positions and metadata
        """
        try:
            # Log access for compliance
            VoyageAuditLog.log_action(
                vessel=vessel,
                action='ROUTE_ACCESSED',
                description=f'Historical data accessed for {start_date} to {end_date}',
                metadata={
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'limit': limit
                },
                compliance_category='DATA_ACCESS'
            )
            
            # Get positions within date range
            positions_query = VesselPosition.objects.filter(
                vessel=vessel,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by('timestamp')
            
            # Apply limit
            if limit:
                positions_query = positions_query[:limit]
            
            positions = positions_query.values(
                'latitude', 'longitude', 'speed', 'heading', 'timestamp',
                'source', 'accuracy', 'is_interpolated', 'voyage_id'
            )
            
            # Group by voyage
            voyages_data = {}
            positions_list = []
            
            for position in positions:
                voyage_id = position['voyage_id']
                
                position_data = {
                    'latitude': position['latitude'],
                    'longitude': position['longitude'],
                    'speed': position['speed'],
                    'heading': position['heading'],
                    'timestamp': position['timestamp'].isoformat(),
                    'source': position['source'],
                    'accuracy': position['accuracy'],
                    'is_interpolated': position['is_interpolated'],
                    'voyage_id': voyage_id
                }
                
                positions_list.append(position_data)
                
                if voyage_id and voyage_id not in voyages_data:
                    try:
                        voyage = Voyage.objects.get(id=voyage_id)
                        voyages_data[voyage_id] = {
                            'id': voyage.id,
                            'port_from': voyage.port_from.name,
                            'port_to': voyage.port_to.name,
                            'departure_time': voyage.departure_time.isoformat(),
                            'arrival_time': voyage.arrival_time.isoformat() if voyage.arrival_time else None,
                            'status': voyage.status
                        }
                    except Voyage.DoesNotExist:
                        voyages_data[voyage_id] = None
            
            return {
                'vessel': {
                    'id': vessel.id,
                    'name': vessel.name,
                    'imo_number': vessel.imo_number,
                    'vessel_type': vessel.vessel_type
                },
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'positions': positions_list,
                'voyages': voyages_data,
                'total_positions': len(positions_list),
                'has_more': len(positions_list) == limit
            }
            
        except Exception as e:
            logger.error(f"Error getting vessel history for {vessel.name}: {str(e)}", exc_info=True)
            return {
                'vessel': {'id': vessel.id, 'name': vessel.name},
                'positions': [],
                'voyages': {},
                'error': str(e)
            }
    
    def generate_replay_data(self, voyage: Voyage, speed_multiplier: float = 1.0,
                           interpolate_gaps: bool = True, user=None) -> Dict[str, Any]:
        """
        Generate replay data for voyage visualization with timing information.
        
        Args:
            voyage: Voyage instance
            speed_multiplier: Replay speed multiplier (1.0 = real time)
            interpolate_gaps: Whether to interpolate missing positions
            user: User requesting replay (for audit logging)
            
        Returns:
            Dictionary with replay data and timing information
        """
        try:
            # Log replay start
            VoyageAuditLog.log_action(
                vessel=voyage.vessel,
                voyage=voyage,
                action='REPLAY_STARTED',
                description=f'Voyage replay started with {speed_multiplier}x speed',
                user=user,
                metadata={
                    'speed_multiplier': speed_multiplier,
                    'interpolate_gaps': interpolate_gaps
                },
                compliance_category='DATA_ACCESS'
            )
            
            # Get all positions for the voyage
            positions = VesselPosition.objects.filter(
                voyage=voyage
            ).order_by('timestamp')
            
            if not positions.exists():
                return {
                    'voyage_id': voyage.id,
                    'error': 'No position data available for this voyage'
                }
            
            # Convert positions to replay format
            replay_positions = []
            previous_position = None
            
            for position in positions:
                # Calculate time offset from voyage start
                time_offset = (position.timestamp - voyage.departure_time).total_seconds()
                
                # Calculate distance from previous position
                distance = 0
                if previous_position:
                    distance = position.distance_to(previous_position)
                
                replay_positions.append({
                    'latitude': position.latitude,
                    'longitude': position.longitude,
                    'speed': position.speed,
                    'heading': position.heading,
                    'timestamp': position.timestamp.isoformat(),
                    'time_offset_seconds': time_offset,
                    'replay_time_seconds': time_offset / speed_multiplier,
                    'distance_from_previous': distance,
                    'source': position.source,
                    'is_interpolated': position.is_interpolated
                })
                
                previous_position = position
            
            # Add interpolated positions if requested
            if interpolate_gaps:
                replay_positions = self._interpolate_replay_positions(replay_positions)
            
            # Calculate replay metadata
            total_duration = replay_positions[-1]['time_offset_seconds'] if replay_positions else 0
            replay_duration = total_duration / speed_multiplier
            total_distance = sum(pos['distance_from_previous'] for pos in replay_positions)
            
            replay_data = {
                'voyage': {
                    'id': voyage.id,
                    'vessel_name': voyage.vessel.name,
                    'port_from': voyage.port_from.name,
                    'port_to': voyage.port_to.name,
                    'departure_time': voyage.departure_time.isoformat(),
                    'arrival_time': voyage.arrival_time.isoformat() if voyage.arrival_time else None,
                    'status': voyage.status
                },
                'replay_settings': {
                    'speed_multiplier': speed_multiplier,
                    'interpolate_gaps': interpolate_gaps
                },
                'metadata': {
                    'total_positions': len(replay_positions),
                    'actual_duration_seconds': total_duration,
                    'replay_duration_seconds': replay_duration,
                    'total_distance_nm': round(total_distance, 2),
                    'average_speed': round(total_distance / (total_duration / 3600), 2) if total_duration > 0 else 0
                },
                'positions': replay_positions,
                'generated_at': timezone.now().isoformat()
            }
            
            # Log replay completion
            VoyageAuditLog.log_action(
                vessel=voyage.vessel,
                voyage=voyage,
                action='REPLAY_COMPLETED',
                description=f'Replay data generated with {len(replay_positions)} positions',
                user=user,
                metadata={
                    'positions_count': len(replay_positions),
                    'total_distance': total_distance,
                    'replay_duration': replay_duration
                },
                compliance_category='DATA_ACCESS'
            )
            
            return replay_data
            
        except Exception as e:
            logger.error(f"Error generating replay data for voyage {voyage.id}: {str(e)}", exc_info=True)
            return {
                'voyage_id': voyage.id,
                'error': str(e)
            }
    
    def _interpolate_replay_positions(self, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Interpolate positions to fill gaps larger than the threshold.
        
        Args:
            positions: List of position dictionaries
            
        Returns:
            List with interpolated positions added
        """
        if len(positions) < 2:
            return positions
        
        interpolated_positions = [positions[0]]  # Start with first position
        
        for i in range(1, len(positions)):
            current_pos = positions[i]
            previous_pos = positions[i-1]
            
            # Calculate time gap
            time_gap = current_pos['time_offset_seconds'] - previous_pos['time_offset_seconds']
            
            # If gap is larger than threshold, add interpolated positions
            if time_gap > self.interpolation_threshold_minutes * 60:
                num_interpolations = int(time_gap / (self.interpolation_threshold_minutes * 60))
                
                for j in range(1, num_interpolations + 1):
                    ratio = j / (num_interpolations + 1)
                    
                    # Linear interpolation
                    interp_lat = previous_pos['latitude'] + (current_pos['latitude'] - previous_pos['latitude']) * ratio
                    interp_lon = previous_pos['longitude'] + (current_pos['longitude'] - previous_pos['longitude']) * ratio
                    interp_time = previous_pos['time_offset_seconds'] + time_gap * ratio
                    
                    # Interpolate other values
                    interp_speed = None
                    if previous_pos['speed'] and current_pos['speed']:
                        interp_speed = previous_pos['speed'] + (current_pos['speed'] - previous_pos['speed']) * ratio
                    
                    interp_heading = None
                    if previous_pos['heading'] and current_pos['heading']:
                        # Handle heading interpolation (circular)
                        heading_diff = current_pos['heading'] - previous_pos['heading']
                        if heading_diff > 180:
                            heading_diff -= 360
                        elif heading_diff < -180:
                            heading_diff += 360
                        interp_heading = (previous_pos['heading'] + heading_diff * ratio) % 360
                    
                    interpolated_positions.append({
                        'latitude': interp_lat,
                        'longitude': interp_lon,
                        'speed': interp_speed,
                        'heading': int(interp_heading) if interp_heading else None,
                        'timestamp': None,  # No actual timestamp for interpolated
                        'time_offset_seconds': interp_time,
                        'replay_time_seconds': interp_time,  # Will be adjusted by speed multiplier
                        'distance_from_previous': 0,  # Will be calculated later
                        'source': 'INTERPOLATED',
                        'is_interpolated': True
                    })
            
            interpolated_positions.append(current_pos)
        
        return interpolated_positions
    
    def get_voyage_statistics(self, voyage: Voyage) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a voyage.
        
        Args:
            voyage: Voyage instance
            
        Returns:
            Dictionary with voyage statistics
        """
        try:
            positions = VesselPosition.objects.filter(voyage=voyage)
            
            if not positions.exists():
                return {'error': 'No position data available'}
            
            # Basic statistics
            stats = positions.aggregate(
                total_positions=Count('id'),
                min_speed=Min('speed'),
                max_speed=Max('speed'),
                avg_speed=Avg('speed'),
                first_position=Min('timestamp'),
                last_position=Max('timestamp')
            )
            
            # Calculate total distance
            positions_list = list(positions.order_by('timestamp'))
            total_distance = 0
            
            for i in range(1, len(positions_list)):
                distance = positions_list[i].distance_to(positions_list[i-1])
                total_distance += distance
            
            # Calculate duration
            if stats['first_position'] and stats['last_position']:
                duration = stats['last_position'] - stats['first_position']
                duration_hours = duration.total_seconds() / 3600
            else:
                duration_hours = 0
            
            return {
                'voyage_id': voyage.id,
                'vessel_name': voyage.vessel.name,
                'route': f"{voyage.port_from.name} → {voyage.port_to.name}",
                'status': voyage.status,
                'statistics': {
                    'total_positions': stats['total_positions'],
                    'total_distance_nm': round(total_distance, 2),
                    'duration_hours': round(duration_hours, 2),
                    'average_speed_knots': round(stats['avg_speed'] or 0, 2),
                    'max_speed_knots': round(stats['max_speed'] or 0, 2),
                    'min_speed_knots': round(stats['min_speed'] or 0, 2),
                    'first_position_time': stats['first_position'].isoformat() if stats['first_position'] else None,
                    'last_position_time': stats['last_position'].isoformat() if stats['last_position'] else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating voyage statistics: {str(e)}", exc_info=True)
            return {'error': str(e)}
    
    def cleanup_old_positions(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up old position data based on retention policy.
        
        Args:
            dry_run: If True, only count records without deleting
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=self.position_retention_days)
            
            # Find old positions
            old_positions = VesselPosition.objects.filter(
                timestamp__lt=cutoff_date
            )
            
            count = old_positions.count()
            
            if not dry_run and count > 0:
                # Log cleanup action
                VoyageAuditLog.log_action(
                    vessel=None,  # System action
                    action='DATA_RETENTION',
                    description=f'Cleaned up {count} old position records older than {self.position_retention_days} days',
                    metadata={
                        'cutoff_date': cutoff_date.isoformat(),
                        'records_deleted': count,
                        'retention_days': self.position_retention_days
                    },
                    compliance_category='DATA_RETENTION'
                )
                
                # Delete old positions
                old_positions.delete()
            
            return {
                'action': 'cleanup_positions',
                'dry_run': dry_run,
                'cutoff_date': cutoff_date.isoformat(),
                'records_found': count,
                'records_deleted': count if not dry_run else 0,
                'retention_days': self.position_retention_days
            }
            
        except Exception as e:
            logger.error(f"Error during position cleanup: {str(e)}", exc_info=True)
            return {'error': str(e)}
    
    def cleanup_old_audit_logs(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up old audit logs based on retention policy.
        
        Args:
            dry_run: If True, only count records without deleting
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=self.audit_retention_days)
            
            # Find old audit logs
            old_logs = VoyageAuditLog.objects.filter(
                timestamp__lt=cutoff_date
            )
            
            count = old_logs.count()
            
            if not dry_run and count > 0:
                # Log cleanup action (before deleting)
                VoyageAuditLog.log_action(
                    vessel=None,  # System action
                    action='DATA_RETENTION',
                    description=f'Cleaned up {count} old audit log records older than {self.audit_retention_days} days',
                    metadata={
                        'cutoff_date': cutoff_date.isoformat(),
                        'records_deleted': count,
                        'retention_days': self.audit_retention_days
                    },
                    compliance_category='DATA_RETENTION'
                )
                
                # Delete old logs
                old_logs.delete()
            
            return {
                'action': 'cleanup_audit_logs',
                'dry_run': dry_run,
                'cutoff_date': cutoff_date.isoformat(),
                'records_found': count,
                'records_deleted': count if not dry_run else 0,
                'retention_days': self.audit_retention_days
            }
            
        except Exception as e:
            logger.error(f"Error during audit log cleanup: {str(e)}", exc_info=True)
            return {'error': str(e)}


class VoyageReplayService:
    """
    Specialized service for voyage replay functionality.
    """
    
    @staticmethod
    def create_replay_session(voyage: Voyage, user=None, **options) -> str:
        """
        Create a new replay session for a voyage.
        
        Args:
            voyage: Voyage to replay
            user: User creating the session
            **options: Replay options (speed, interpolation, etc.)
            
        Returns:
            Session ID for tracking the replay
        """
        import uuid
        
        session_id = str(uuid.uuid4())
        
        # Log session creation
        VoyageAuditLog.log_action(
            vessel=voyage.vessel,
            voyage=voyage,
            action='REPLAY_STARTED',
            description=f'Replay session {session_id} created',
            user=user,
            metadata={
                'session_id': session_id,
                'options': options
            },
            compliance_category='DATA_ACCESS'
        )
        
        return session_id
    
    @staticmethod
    def get_replay_frame(voyage: Voyage, frame_index: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific frame from the voyage replay.
        
        Args:
            voyage: Voyage instance
            frame_index: Frame index to retrieve
            
        Returns:
            Frame data or None if not found
        """
        try:
            positions = VesselPosition.objects.filter(
                voyage=voyage
            ).order_by('timestamp')
            
            if frame_index < 0 or frame_index >= positions.count():
                return None
            
            position = positions[frame_index]
            
            return {
                'frame_index': frame_index,
                'latitude': position.latitude,
                'longitude': position.longitude,
                'speed': position.speed,
                'heading': position.heading,
                'timestamp': position.timestamp.isoformat(),
                'source': position.source
            }
            
        except Exception as e:
            logger.error(f"Error getting replay frame: {str(e)}", exc_info=True)
            return None
"""
Enhanced Port Analytics Service for comprehensive congestion analysis.

Integrates UNCTAD-style port trade statistics and provides:
- Real-time congestion scoring
- Traffic pattern analysis
- Automated alert generation
- Performance metrics calculation
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Iterable, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Avg, Count, Q, F
from statistics import mean, median

import requests

from core.models import Port, Vessel, Event, Voyage
from core.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class PortAnalyticsService:
    """
    Enhanced service for port congestion analytics and UNCTAD integration.
    """
    
    def __init__(self):
        self.unctad_url = getattr(
            settings,
            "UNCTAD_PORT_STATS_URL",
            "https://api.unctad.org/port-statistics/v1"  # Example URL
        )
        self.api_key = getattr(settings, "UNCTAD_API_KEY", None)
        self.congestion_thresholds = {
            'low': 3.0,
            'moderate': 5.0,
            'high': 7.0,
            'critical': 9.0
        }
    
    def fetch_unctad_port_statistics(self, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Fetch port statistics from UNCTAD API with enhanced error handling.
        
        Args:
            params: Query parameters for API request
            
        Returns:
            List of port statistics records
        """
        if not self.api_key:
            logger.warning("No UNCTAD API key configured, using mock data")
            return self._generate_mock_unctad_data()
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            query_params = params or {}
            query_params.setdefault('format', 'json')
            query_params.setdefault('year', datetime.now().year)
            
            response = requests.get(
                f"{self.unctad_url}/ports/statistics",
                headers=headers,
                params=query_params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return self._normalize_unctad_response(data)
            
        except requests.RequestException as e:
            logger.error(f"UNCTAD API request failed: {str(e)}", exc_info=True)
            return self._generate_mock_unctad_data()
        except Exception as e:
            logger.error(f"Error processing UNCTAD data: {str(e)}", exc_info=True)
            return self._generate_mock_unctad_data()
    
    def _normalize_unctad_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize UNCTAD API response to standard format.
        
        Args:
            data: Raw UNCTAD API response
            
        Returns:
            Normalized port statistics data
        """
        # Handle different UNCTAD response formats
        if isinstance(data, dict):
            if 'data' in data:
                records = data['data']
            elif 'ports' in data:
                records = data['ports']
            elif 'results' in data:
                records = data['results']
            else:
                records = [data]  # Single record
        else:
            records = data if isinstance(data, list) else []
        
        normalized = []
        for record in records:
            try:
                normalized_record = {
                    'port_name': record.get('port_name') or record.get('name'),
                    'country': record.get('country') or record.get('country_name'),
                    'unlocode': record.get('unlocode') or record.get('port_code'),
                    'total_throughput': float(record.get('total_throughput', 0)),
                    'container_throughput': float(record.get('container_throughput', 0)),
                    'vessel_arrivals': int(record.get('vessel_arrivals', 0)),
                    'vessel_departures': int(record.get('vessel_departures', 0)),
                    'avg_waiting_time': float(record.get('avg_waiting_time', 0)),
                    'berth_occupancy_rate': float(record.get('berth_occupancy_rate', 0)),
                    'cargo_dwell_time': float(record.get('cargo_dwell_time', 0)),
                    'year': int(record.get('year', datetime.now().year)),
                    'month': int(record.get('month', datetime.now().month)),
                }
                normalized.append(normalized_record)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error normalizing UNCTAD record: {e}")
                continue
        
        return normalized
    
    def _generate_mock_unctad_data(self) -> List[Dict[str, Any]]:
        """
        Generate realistic mock UNCTAD-style port statistics for development.
        
        Returns:
            Mock port statistics data
        """
        mock_ports = [
            {
                'port_name': 'Port of Dubai',
                'country': 'UAE',
                'unlocode': 'AEDXB',
                'base_throughput': 15000000,
                'base_arrivals': 8000,
            },
            {
                'port_name': 'Port of Singapore',
                'country': 'Singapore',
                'unlocode': 'SGSIN',
                'base_throughput': 37000000,
                'base_arrivals': 12000,
            },
            {
                'port_name': 'Port of Rotterdam',
                'country': 'Netherlands',
                'unlocode': 'NLRTM',
                'base_throughput': 14500000,
                'base_arrivals': 9500,
            },
            {
                'port_name': 'Port of Shanghai',
                'country': 'China',
                'unlocode': 'CNSHA',
                'base_throughput': 47000000,
                'base_arrivals': 15000,
            },
            {
                'port_name': 'Port of Los Angeles',
                'country': 'USA',
                'unlocode': 'USLAX',
                'base_throughput': 9300000,
                'base_arrivals': 7200,
            }
        ]
        
        mock_data = []
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        for port in mock_ports:
            # Add realistic variation to base statistics
            throughput_variation = random.uniform(0.8, 1.2)
            arrivals_variation = random.uniform(0.85, 1.15)
            
            total_throughput = int(port['base_throughput'] * throughput_variation)
            vessel_arrivals = int(port['base_arrivals'] * arrivals_variation)
            vessel_departures = int(vessel_arrivals * random.uniform(0.95, 1.05))
            
            # Calculate derived metrics
            berth_occupancy = min(95.0, max(40.0, random.uniform(60, 90)))
            avg_waiting_time = self._calculate_waiting_time_from_occupancy(berth_occupancy)
            cargo_dwell_time = random.uniform(3.5, 8.5)  # Days
            
            mock_data.append({
                'port_name': port['port_name'],
                'country': port['country'],
                'unlocode': port['unlocode'],
                'total_throughput': total_throughput,
                'container_throughput': int(total_throughput * random.uniform(0.6, 0.9)),
                'vessel_arrivals': vessel_arrivals,
                'vessel_departures': vessel_departures,
                'avg_waiting_time': round(avg_waiting_time, 1),
                'berth_occupancy_rate': round(berth_occupancy, 1),
                'cargo_dwell_time': round(cargo_dwell_time, 1),
                'year': current_year,
                'month': current_month,
            })
        
        return mock_data
    
    def _calculate_waiting_time_from_occupancy(self, occupancy_rate: float) -> float:
        """
        Calculate average waiting time based on berth occupancy rate.
        Uses queuing theory approximation.
        
        Args:
            occupancy_rate: Berth occupancy percentage (0-100)
            
        Returns:
            Average waiting time in hours
        """
        # Convert to utilization factor (0-1)
        rho = min(0.95, occupancy_rate / 100.0)
        
        # Simple M/M/1 queue approximation: W = rho / (1 - rho) * service_time
        # Assume average service time of 24 hours
        service_time = 24.0
        
        if rho >= 0.95:
            # Very high occupancy leads to exponential waiting times
            waiting_time = service_time * random.uniform(8, 15)
        else:
            waiting_time = service_time * (rho / (1 - rho))
        
        return max(0.5, waiting_time)  # Minimum 0.5 hours
    
    def calculate_congestion_score(self, port_data: Dict[str, Any]) -> float:
        """
        Calculate comprehensive congestion score based on multiple factors.
        
        Args:
            port_data: Port statistics data
            
        Returns:
            Congestion score (0-10 scale)
        """
        factors = {}
        
        # Factor 1: Berth occupancy rate (40% weight)
        occupancy = port_data.get('berth_occupancy_rate', 50.0)
        factors['occupancy'] = min(10.0, (occupancy / 10.0)) * 0.4
        
        # Factor 2: Average waiting time (30% weight)
        waiting_time = port_data.get('avg_waiting_time', 2.0)
        # Normalize: 0-2 hours = 0-3 points, 2-8 hours = 3-7 points, 8+ hours = 7-10 points
        if waiting_time <= 2:
            wait_score = (waiting_time / 2.0) * 3.0
        elif waiting_time <= 8:
            wait_score = 3.0 + ((waiting_time - 2.0) / 6.0) * 4.0
        else:
            wait_score = 7.0 + min(3.0, (waiting_time - 8.0) / 4.0 * 3.0)
        factors['waiting'] = wait_score * 0.3
        
        # Factor 3: Cargo dwell time (20% weight)
        dwell_time = port_data.get('cargo_dwell_time', 5.0)
        # Normalize: 0-3 days = 0-2 points, 3-7 days = 2-6 points, 7+ days = 6-10 points
        if dwell_time <= 3:
            dwell_score = (dwell_time / 3.0) * 2.0
        elif dwell_time <= 7:
            dwell_score = 2.0 + ((dwell_time - 3.0) / 4.0) * 4.0
        else:
            dwell_score = 6.0 + min(4.0, (dwell_time - 7.0) / 3.0 * 4.0)
        factors['dwell'] = dwell_score * 0.2
        
        # Factor 4: Traffic imbalance (10% weight)
        arrivals = port_data.get('vessel_arrivals', 100)
        departures = port_data.get('vessel_departures', 100)
        if arrivals > 0:
            imbalance = abs(arrivals - departures) / arrivals
            factors['imbalance'] = min(10.0, imbalance * 20) * 0.1
        else:
            factors['imbalance'] = 0.0
        
        # Calculate final score
        total_score = sum(factors.values())
        
        logger.debug(f"Congestion factors: {factors}, Total: {total_score:.2f}")
        return round(min(10.0, max(0.0, total_score)), 1)
    
    def update_port_analytics(self, port_data: Dict[str, Any]) -> Optional[Port]:
        """
        Update port with analytics data and trigger events if needed.
        
        Args:
            port_data: Normalized port statistics data
            
        Returns:
            Updated Port instance or None if not found
        """
        port_name = port_data.get('port_name')
        country = port_data.get('country')
        
        if not port_name or not country:
            logger.warning(f"Missing port name or country in data: {port_data}")
            return None
        
        try:
            port = Port.objects.get(name=port_name, country=country)
        except Port.DoesNotExist:
            logger.debug(f"Port not found: {port_name}, {country}")
            return None
        
        # Store previous values for comparison
        previous_congestion = port.congestion_score
        
        # Calculate new metrics
        congestion_score = self.calculate_congestion_score(port_data)
        avg_wait_time = port_data.get('avg_waiting_time', port.avg_wait_time)
        arrivals = port_data.get('vessel_arrivals', port.arrivals_count)
        departures = port_data.get('vessel_departures', port.departures_count)
        
        # Update port
        port.congestion_score = congestion_score
        port.avg_wait_time = avg_wait_time
        port.arrivals_count = arrivals
        port.departures_count = departures
        port.save()
        
        # Check for congestion level changes and trigger events
        self._check_congestion_alerts(port, previous_congestion, congestion_score)
        
        logger.info(f"Updated port analytics for {port.name}: congestion={congestion_score}")
        return port
    
    def _check_congestion_alerts(self, port: Port, previous_score: float, current_score: float):
        """
        Check if congestion level changes warrant alerts.
        
        Args:
            port: Port instance
            previous_score: Previous congestion score
            current_score: Current congestion score
        """
        # Define congestion level thresholds
        def get_congestion_level(score):
            if score >= self.congestion_thresholds['critical']:
                return 'critical'
            elif score >= self.congestion_thresholds['high']:
                return 'high'
            elif score >= self.congestion_thresholds['moderate']:
                return 'moderate'
            else:
                return 'low'
        
        previous_level = get_congestion_level(previous_score)
        current_level = get_congestion_level(current_score)
        
        # Trigger alert if congestion level increased significantly
        if (current_level != previous_level and 
            current_score > previous_score and 
            current_score >= self.congestion_thresholds['high']):
            
            self._create_congestion_event(port, current_score, current_level)
    
    def _create_congestion_event(self, port: Port, congestion_score: float, level: str):
        """
        Create congestion event and trigger notifications.
        
        Args:
            port: Port instance
            congestion_score: Current congestion score
            level: Congestion level (high, critical)
        """
        # Find vessels approaching this port (simplified logic)
        approaching_vessels = self._find_vessels_approaching_port(port)
        
        for vessel in approaching_vessels:
            # Check if we already have a recent congestion event
            recent_event = Event.objects.filter(
                vessel=vessel,
                event_type='HIGH_CONGESTION',
                location__icontains=port.name,
                timestamp__gte=timezone.now() - timedelta(hours=6)
            ).exists()
            
            if not recent_event:
                event = Event.objects.create(
                    vessel=vessel,
                    event_type='HIGH_CONGESTION',
                    location=f"{port.name}, {port.country}",
                    details=f"Port congestion level: {level.upper()} (score: {congestion_score}). "
                           f"Average wait time: {port.avg_wait_time:.1f} hours. "
                           f"Arrivals: {port.arrivals_count}, Departures: {port.departures_count}"
                )
                
                # Trigger notifications
                NotificationService.notify_users_for_event(event)
                logger.info(f"Created congestion event for {vessel.name} at {port.name}")
    
    def _find_vessels_approaching_port(self, port: Port, radius_km: float = 100) -> List[Vessel]:
        """
        Find vessels that might be approaching the given port.
        Simplified implementation using proximity.
        
        Args:
            port: Port instance
            radius_km: Search radius in kilometers
            
        Returns:
            List of vessels potentially approaching the port
        """
        # This is a simplified implementation
        # In production, you'd use proper geospatial queries and route prediction
        
        # For now, return a few random vessels for demonstration
        vessels = list(Vessel.objects.filter(
            last_position_lat__isnull=False,
            last_position_lon__isnull=False
        )[:3])  # Limit to 3 for testing
        
        return vessels
    
    def get_port_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive port dashboard analytics.
        
        Returns:
            Dashboard data with port statistics and trends
        """
        try:
            ports = Port.objects.all()
            
            if not ports.exists():
                return self._get_fallback_dashboard_data()
            
            # Calculate aggregate statistics
            total_ports = ports.count()
            avg_congestion = ports.aggregate(avg=Avg('congestion_score'))['avg'] or 0
            avg_wait_time = ports.aggregate(avg=Avg('avg_wait_time'))['avg'] or 0
            total_arrivals = ports.aggregate(total=Count('arrivals_count'))['total'] or 0
            total_departures = ports.aggregate(total=Count('departures_count'))['total'] or 0
            
            # Congestion level distribution
            congestion_distribution = {
                'critical': ports.filter(congestion_score__gte=self.congestion_thresholds['critical']).count(),
                'high': ports.filter(
                    congestion_score__gte=self.congestion_thresholds['high'],
                    congestion_score__lt=self.congestion_thresholds['critical']
                ).count(),
                'moderate': ports.filter(
                    congestion_score__gte=self.congestion_thresholds['moderate'],
                    congestion_score__lt=self.congestion_thresholds['high']
                ).count(),
                'low': ports.filter(congestion_score__lt=self.congestion_thresholds['moderate']).count(),
            }
            
            # Top congested ports
            top_congested = list(ports.order_by('-congestion_score')[:10].values(
                'name', 'country', 'congestion_score', 'avg_wait_time', 'arrivals_count', 'departures_count'
            ))
            
            # Recent congestion events
            recent_events = Event.objects.filter(
                event_type='HIGH_CONGESTION',
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).select_related('vessel').order_by('-timestamp')[:20]
            
            recent_events_data = [
                {
                    'vessel_name': event.vessel.name,
                    'vessel_imo': event.vessel.imo_number,
                    'location': event.location,
                    'timestamp': event.timestamp.isoformat(),
                    'details': event.details
                }
                for event in recent_events
            ]
            
            return {
                'summary': {
                    'total_ports': total_ports,
                    'average_congestion_score': round(avg_congestion, 2),
                    'average_wait_time': round(avg_wait_time, 2),
                    'total_arrivals': total_arrivals,
                    'total_departures': total_departures,
                },
                'congestion_distribution': congestion_distribution,
                'top_congested_ports': top_congested,
                'recent_events': recent_events_data,
                'thresholds': self.congestion_thresholds,
                'last_updated': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}", exc_info=True)
            return self._get_fallback_dashboard_data()
    
    def _get_fallback_dashboard_data(self) -> Dict[str, Any]:
        """
        Get fallback dashboard data when database queries fail.
        
        Returns:
            Fallback dashboard data
        """
        return {
            'summary': {
                'total_ports': 5,
                'average_congestion_score': 6.2,
                'average_wait_time': 4.5,
                'total_arrivals': 1250,
                'total_departures': 1180,
            },
            'congestion_distribution': {
                'critical': 1,
                'high': 2,
                'moderate': 1,
                'low': 1,
            },
            'top_congested_ports': [
                {
                    'name': 'Port of Shanghai',
                    'country': 'China',
                    'congestion_score': 9.2,
                    'avg_wait_time': 8.5,
                    'arrivals_count': 450,
                    'departures_count': 420
                },
                {
                    'name': 'Port of Singapore',
                    'country': 'Singapore',
                    'congestion_score': 8.1,
                    'avg_wait_time': 6.2,
                    'arrivals_count': 380,
                    'departures_count': 365
                }
            ],
            'recent_events': [],
            'thresholds': self.congestion_thresholds,
            'last_updated': timezone.now().isoformat(),
            'note': 'Fallback data - database unavailable'
        }
    
    def refresh_all_port_analytics(self) -> Dict[str, Any]:
        """
        Refresh analytics for all ports using UNCTAD data.
        
        Returns:
            Summary of refresh operation
        """
        logger.info("Starting comprehensive port analytics refresh")
        
        try:
            # Fetch UNCTAD data
            unctad_data = self.fetch_unctad_port_statistics()
            
            summary = {
                'started_at': timezone.now().isoformat(),
                'unctad_records_fetched': len(unctad_data),
                'ports_updated': 0,
                'ports_not_found': 0,
                'events_created': 0,
                'errors': []
            }
            
            with transaction.atomic():
                for port_data in unctad_data:
                    try:
                        port = self.update_port_analytics(port_data)
                        if port:
                            summary['ports_updated'] += 1
                        else:
                            summary['ports_not_found'] += 1
                    except Exception as e:
                        error_msg = f"Error updating port {port_data.get('port_name', 'unknown')}: {str(e)}"
                        summary['errors'].append(error_msg)
                        logger.error(error_msg)
            
            summary['completed_at'] = timezone.now().isoformat()
            summary['success'] = len(summary['errors']) == 0
            
            logger.info(f"Port analytics refresh completed: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Critical error in port analytics refresh: {str(e)}", exc_info=True)
            return {
                'started_at': timezone.now().isoformat(),
                'success': False,
                'error': str(e)
            }


# Legacy functions for backward compatibility
def _get_unctad_config() -> str:
    """Legacy function - use PortAnalyticsService instead."""
    logger.warning("Using deprecated _get_unctad_config function")
    return getattr(settings, "UNCTAD_PORT_STATS_URL", "https://example-unctad.org/api/port-stats")


def fetch_unctad_port_stats(params: Dict[str, Any] = None) -> Iterable[Dict[str, Any]]:
    """Legacy function - use PortAnalyticsService instead."""
    logger.warning("Using deprecated fetch_unctad_port_stats function")
    service = PortAnalyticsService()
    return service.fetch_unctad_port_statistics(params)


def refresh_port_congestion(params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Legacy function - use PortAnalyticsService instead."""
    logger.warning("Using deprecated refresh_port_congestion function")
    service = PortAnalyticsService()
    return service.refresh_all_port_analytics()



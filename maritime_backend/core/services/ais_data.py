"""
Enhanced AIS Data Service for fetching real-time vessel position data.
Supports MarineTraffic, AISHub, and other AIS providers with robust error handling.
"""
import logging
import random
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class AISDataService:
    """
    Enhanced service for fetching AIS (Automatic Identification System) vessel data.
    Supports multiple AIS providers with fallback to mock data for development.
    """
    
    def __init__(self, api_key: str = None, provider: str = 'marinetraffic'):
        """
        Initialize AIS data service.
        
        Args:
            api_key: API key for external AIS provider
            provider: AIS provider ('marinetraffic', 'aishub', 'vesselfinder')
        """
        self.api_key = api_key or getattr(settings, 'AIS_API_KEY', None)
        self.provider = provider.lower()
        self.base_urls = {
            'marinetraffic': 'https://services.marinetraffic.com/api',
            'aishub': 'http://data.aishub.net/ws.php',
            'vesselfinder': 'https://api.vesselfinder.com/api',
        }
        self.mock_vessels = self._generate_mock_vessels()
        
        if not self.api_key:
            logger.warning(f"No API key configured for {provider}. Using mock data.")
    
    def _generate_mock_vessels(self) -> List[Dict[str, Any]]:
        """Generate enhanced mock vessel data for testing purposes."""
        mock_data = [
            {
                'imo': '9123456',
                'mmsi': '123456789',
                'name': 'ATLANTIC STAR',
                'vessel_type': 'Container Ship',
                'flag': 'Panama',
                'base_lat': 40.7128,
                'base_lon': -74.0060,
            },
            {
                'imo': '9234567',
                'mmsi': '234567890',
                'name': 'PACIFIC GLORY',
                'vessel_type': 'Bulk Carrier',
                'flag': 'Liberia',
                'base_lat': 34.0522,
                'base_lon': -118.2437,
            },
            {
                'imo': '9345678',
                'mmsi': '345678901',
                'name': 'NORDIC WIND',
                'vessel_type': 'Tanker',
                'flag': 'Marshall Islands',
                'base_lat': 51.5074,
                'base_lon': -0.1278,
            },
            {
                'imo': '9456789',
                'mmsi': '456789012',
                'name': 'SOUTHERN CROSS',
                'vessel_type': 'General Cargo',
                'flag': 'Singapore',
                'base_lat': -33.8688,
                'base_lon': 151.2093,
            },
            {
                'imo': '9567890',
                'mmsi': '567890123',
                'name': 'ARCTIC EXPLORER',
                'vessel_type': 'Research Vessel',
                'flag': 'Norway',
                'base_lat': 60.1699,
                'base_lon': 24.9384,
            },
            {
                'imo': '9678901',
                'mmsi': '678901234',
                'name': 'GULF TRADER',
                'vessel_type': 'Container Ship',
                'flag': 'UAE',
                'base_lat': 25.2048,
                'base_lon': 55.2708,
            },
            {
                'imo': '9789012',
                'mmsi': '789012345',
                'name': 'MEDITERRANEAN STAR',
                'vessel_type': 'Cruise Ship',
                'flag': 'Italy',
                'base_lat': 41.9028,
                'base_lon': 12.4964,
            }
        ]
        return mock_data
    
    def get_live_vessel_positions(self, limit: int = 50, bbox: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Fetch live vessel position data from AIS provider.
        
        Args:
            limit: Maximum number of vessels to return
            bbox: Bounding box filter {'min_lat', 'max_lat', 'min_lon', 'max_lon'}
            
        Returns:
            List of vessel position dictionaries with standardized fields
        """
        try:
            if self.api_key and self.provider in self.base_urls:
                return self._fetch_from_real_api(limit, bbox)
            else:
                logger.info("Using mock data for AIS vessel positions")
                return self._generate_mock_positions(limit, bbox)
        except Exception as e:
            logger.error(f"Error fetching vessel positions: {str(e)}", exc_info=True)
            return self._generate_mock_positions(limit, bbox)
    
    def _fetch_from_real_api(self, limit: int, bbox: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Fetch data from real AIS API with provider-specific implementations.
        """
        try:
            if self.provider == 'marinetraffic':
                return self._fetch_from_marinetraffic(limit, bbox)
            elif self.provider == 'aishub':
                return self._fetch_from_aishub(limit, bbox)
            elif self.provider == 'vesselfinder':
                return self._fetch_from_vesselfinder(limit, bbox)
            else:
                logger.warning(f"Unknown provider: {self.provider}")
                return self._generate_mock_positions(limit, bbox)
        except Exception as e:
            logger.error(f"API fetch failed for {self.provider}: {str(e)}", exc_info=True)
            return self._generate_mock_positions(limit, bbox)
    
    def _fetch_from_marinetraffic(self, limit: int, bbox: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Fetch from MarineTraffic API."""
        url = f"{self.base_urls['marinetraffic']}/exportvessels/{self.api_key}/v:3/protocol:json"
        
        params = {
            'limit': limit,
            'timespan': 10,  # Minutes
        }
        
        if bbox:
            params.update({
                'minlat': bbox['min_lat'],
                'maxlat': bbox['max_lat'],
                'minlon': bbox['min_lon'],
                'maxlon': bbox['max_lon'],
            })
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return self._normalize_marinetraffic_response(data)
    
    def _fetch_from_aishub(self, limit: int, bbox: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Fetch from AISHub API."""
        params = {
            'username': self.api_key,
            'format': '1',  # JSON format
            'output': 'json',
            'compress': '0',
            'limit': limit,
        }
        
        if bbox:
            params.update({
                'latmin': bbox['min_lat'],
                'latmax': bbox['max_lat'],
                'lonmin': bbox['min_lon'],
                'lonmax': bbox['max_lon'],
            })
        
        response = requests.get(self.base_urls['aishub'], params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return self._normalize_aishub_response(data)
    
    def _fetch_from_vesselfinder(self, limit: int, bbox: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Fetch from VesselFinder API."""
        headers = {'Authorization': f'Bearer {self.api_key}'}
        params = {'limit': limit}
        
        if bbox:
            params['bbox'] = f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
        
        response = requests.get(f"{self.base_urls['vesselfinder']}/vessels", 
                              headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return self._normalize_vesselfinder_response(data)
    
    def _normalize_marinetraffic_response(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize MarineTraffic API response to standard format."""
        normalized = []
        for vessel in data:
            try:
                normalized.append({
                    'imo': vessel.get('IMO', ''),
                    'mmsi': vessel.get('MMSI', ''),
                    'name': vessel.get('SHIPNAME', ''),
                    'vessel_type': vessel.get('TYPE_NAME', ''),
                    'flag': vessel.get('FLAG', ''),
                    'latitude': float(vessel.get('LAT', 0)),
                    'longitude': float(vessel.get('LON', 0)),
                    'speed': float(vessel.get('SPEED', 0)),
                    'heading': int(vessel.get('COURSE', 0)),
                    'timestamp': vessel.get('TIMESTAMP', datetime.now(timezone.utc).isoformat()),
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error normalizing MarineTraffic vessel data: {e}")
                continue
        return normalized
    
    def _normalize_aishub_response(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize AISHub API response to standard format."""
        normalized = []
        vessels = data.get('data', []) if isinstance(data, dict) else data
        
        for vessel in vessels:
            try:
                normalized.append({
                    'imo': vessel.get('IMO', ''),
                    'mmsi': vessel.get('MMSI', ''),
                    'name': vessel.get('NAME', ''),
                    'vessel_type': vessel.get('TYPE', ''),
                    'flag': vessel.get('COUNTRY', ''),
                    'latitude': float(vessel.get('LATITUDE', 0)),
                    'longitude': float(vessel.get('LONGITUDE', 0)),
                    'speed': float(vessel.get('SOG', 0)),  # Speed Over Ground
                    'heading': int(vessel.get('COG', 0)),  # Course Over Ground
                    'timestamp': vessel.get('TIME', datetime.now(timezone.utc).isoformat()),
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error normalizing AISHub vessel data: {e}")
                continue
        return normalized
    
    def _normalize_vesselfinder_response(self, data: Dict) -> List[Dict[str, Any]]:
        """Normalize VesselFinder API response to standard format."""
        normalized = []
        vessels = data.get('vessels', [])
        
        for vessel in vessels:
            try:
                normalized.append({
                    'imo': vessel.get('imo', ''),
                    'mmsi': vessel.get('mmsi', ''),
                    'name': vessel.get('name', ''),
                    'vessel_type': vessel.get('type', ''),
                    'flag': vessel.get('flag', ''),
                    'latitude': float(vessel.get('lat', 0)),
                    'longitude': float(vessel.get('lon', 0)),
                    'speed': float(vessel.get('speed', 0)),
                    'heading': int(vessel.get('heading', 0)),
                    'timestamp': vessel.get('timestamp', datetime.now(timezone.utc).isoformat()),
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error normalizing VesselFinder vessel data: {e}")
                continue
        return normalized
    
    def _generate_mock_positions(self, limit: int, bbox: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Generate mock vessel positions for testing with realistic movement."""
        positions = []
        
        vessels_to_use = self.mock_vessels[:limit]
        
        for vessel in vessels_to_use:
            # Add realistic movement simulation
            lat_offset = random.uniform(-0.05, 0.05)
            lon_offset = random.uniform(-0.05, 0.05)
            
            lat = vessel['base_lat'] + lat_offset
            lon = vessel['base_lon'] + lon_offset
            
            # Apply bounding box filter if provided
            if bbox:
                if not (bbox['min_lat'] <= lat <= bbox['max_lat'] and 
                       bbox['min_lon'] <= lon <= bbox['max_lon']):
                    continue
            
            position = {
                'imo': vessel['imo'],
                'mmsi': vessel['mmsi'],
                'name': vessel['name'],
                'vessel_type': vessel['vessel_type'],
                'flag': vessel['flag'],
                'latitude': round(lat, 6),
                'longitude': round(lon, 6),
                'speed': round(random.uniform(0, 25), 1),
                'heading': random.randint(0, 359),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            positions.append(position)
        
        return positions
    
    def get_vessel_by_imo(self, imo: str) -> Optional[Dict[str, Any]]:
        """
        Get specific vessel data by IMO number.
        
        Args:
            imo: IMO number of the vessel
            
        Returns:
            Vessel position data or None if not found
        """
        try:
            if self.api_key and self.provider in self.base_urls:
                return self._fetch_vessel_by_imo_from_api(imo)
            else:
                return self._get_mock_vessel_by_imo(imo)
        except Exception as e:
            logger.error(f"Error fetching vessel {imo}: {str(e)}", exc_info=True)
            return self._get_mock_vessel_by_imo(imo)
    
    def _fetch_vessel_by_imo_from_api(self, imo: str) -> Optional[Dict[str, Any]]:
        """Fetch specific vessel from real API by IMO."""
        # For most APIs, we need to fetch all vessels and filter
        # Some APIs support direct IMO lookup
        all_positions = self.get_live_vessel_positions(limit=1000)
        for vessel in all_positions:
            if vessel.get('imo') == imo:
                return vessel
        return None
    
    def _get_mock_vessel_by_imo(self, imo: str) -> Optional[Dict[str, Any]]:
        """Get mock vessel data by IMO."""
        all_positions = self._generate_mock_positions(len(self.mock_vessels))
        for vessel in all_positions:
            if vessel['imo'] == imo:
                return vessel
        return None
    
    def get_vessels_in_area(self, bbox: Dict[str, float], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get vessels within a specific geographical area.
        
        Args:
            bbox: Bounding box {'min_lat', 'max_lat', 'min_lon', 'max_lon'}
            limit: Maximum number of vessels to return
            
        Returns:
            List of vessels within the specified area
        """
        return self.get_live_vessel_positions(limit=limit, bbox=bbox)
    
    def validate_api_connection(self) -> Dict[str, Any]:
        """
        Validate API connection and return status information.
        
        Returns:
            Dictionary with connection status and details
        """
        status = {
            'provider': self.provider,
            'api_key_configured': bool(self.api_key),
            'connection_status': 'unknown',
            'error': None,
            'test_vessel_count': 0
        }
        
        try:
            if not self.api_key:
                status['connection_status'] = 'no_api_key'
                status['error'] = 'No API key configured'
                return status
            
            # Test with a small request
            test_vessels = self.get_live_vessel_positions(limit=1)
            status['test_vessel_count'] = len(test_vessels)
            status['connection_status'] = 'connected' if test_vessels else 'no_data'
            
        except Exception as e:
            status['connection_status'] = 'error'
            status['error'] = str(e)
            logger.error(f"API validation failed: {e}", exc_info=True)
        
        return status
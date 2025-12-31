"""
AIS Data Service for fetching vessel position data.
Currently uses mock data but structured for easy integration with real AIS APIs.
"""
import random
from datetime import datetime, timezone
from typing import List, Dict, Any


class AISDataService:
    """
    Service for fetching AIS (Automatic Identification System) vessel data.
    Currently provides mock data but designed for easy integration with
    real AIS providers like MarineTraffic API.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize AIS data service.
        
        Args:
            api_key: API key for external AIS provider (for future use)
        """
        self.api_key = api_key
        self.mock_vessels = self._generate_mock_vessels()
    
    def _generate_mock_vessels(self) -> List[Dict[str, Any]]:
        """Generate mock vessel data for testing purposes."""
        mock_data = [
            {
                'imo': '9123456',
                'name': 'ATLANTIC STAR',
                'vessel_type': 'Container Ship',
                'base_lat': 40.7128,
                'base_lon': -74.0060,
            },
            {
                'imo': '9234567',
                'name': 'PACIFIC GLORY',
                'vessel_type': 'Bulk Carrier',
                'base_lat': 34.0522,
                'base_lon': -118.2437,
            },
            {
                'imo': '9345678',
                'name': 'NORDIC WIND',
                'vessel_type': 'Tanker',
                'base_lat': 51.5074,
                'base_lon': -0.1278,
            },
            {
                'imo': '9456789',
                'name': 'SOUTHERN CROSS',
                'vessel_type': 'General Cargo',
                'base_lat': -33.8688,
                'base_lon': 151.2093,
            },
            {
                'imo': '9567890',
                'name': 'ARCTIC EXPLORER',
                'vessel_type': 'Research Vessel',
                'base_lat': 60.1699,
                'base_lon': 24.9384,
            }
        ]
        return mock_data
    
    def get_live_vessel_positions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch live vessel position data.
        
        Args:
            limit: Maximum number of vessels to return
            
        Returns:
            List of vessel position dictionaries with required fields:
            - imo: IMO number
            - latitude: Current latitude
            - longitude: Current longitude
            - speed: Speed in knots
            - heading: Heading in degrees (0-359)
            - timestamp: ISO timestamp of last position update
        """
        if self.api_key:
            # TODO: Implement real API call when API key is provided
            return self._fetch_from_real_api(limit)
        else:
            return self._generate_mock_positions(limit)
    
    def _fetch_from_real_api(self, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch data from real AIS API (placeholder for future implementation).
        
        This method would integrate with services like:
        - MarineTraffic API
        - VesselFinder API
        - AISHub API
        """
        # TODO: Implement real API integration
        # Example structure for MarineTraffic API:
        # url = f"https://services.marinetraffic.com/api/exportvessels/{self.api_key}/v:3/protocol:json"
        # response = requests.get(url, params={'limit': limit})
        # return self._parse_api_response(response.json())
        
        # For now, return mock data
        return self._generate_mock_positions(limit)
    
    def _generate_mock_positions(self, limit: int) -> List[Dict[str, Any]]:
        """Generate mock vessel positions for testing."""
        positions = []
        
        for i, vessel in enumerate(self.mock_vessels[:limit]):
            # Add some random variation to base position
            lat_offset = random.uniform(-0.1, 0.1)
            lon_offset = random.uniform(-0.1, 0.1)
            
            position = {
                'imo': vessel['imo'],
                'name': vessel['name'],
                'vessel_type': vessel['vessel_type'],
                'latitude': round(vessel['base_lat'] + lat_offset, 6),
                'longitude': round(vessel['base_lon'] + lon_offset, 6),
                'speed': round(random.uniform(0, 25), 1),  # Speed in knots
                'heading': random.randint(0, 359),  # Heading in degrees
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            positions.append(position)
        
        return positions
    
    def get_vessel_by_imo(self, imo: str) -> Dict[str, Any]:
        """
        Get specific vessel data by IMO number.
        
        Args:
            imo: IMO number of the vessel
            
        Returns:
            Vessel position data or None if not found
        """
        all_positions = self.get_live_vessel_positions()
        for vessel in all_positions:
            if vessel['imo'] == imo:
                return vessel
        return None
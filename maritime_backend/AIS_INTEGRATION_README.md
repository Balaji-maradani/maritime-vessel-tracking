# AIS Data Integration

This document describes the AIS (Automatic Identification System) data integration implemented for the Maritime Backend.

## Overview

The implementation provides a new API endpoint `/api/live-vessels/` that returns real-time vessel position data. Currently uses mock data but is architected for easy integration with real AIS providers like MarineTraffic.

## Implementation Details

### 1. AIS Data Service (`core/services/ais_data.py`)

The `AISDataService` class handles fetching vessel position data:

- **Mock Mode**: Generates realistic test data with 5 sample vessels
- **API Ready**: Structured for easy integration with real AIS APIs
- **Configurable**: Accepts API key parameter for future use

**Key Methods:**
- `get_live_vessel_positions(limit)`: Returns list of vessel positions
- `get_vessel_by_imo(imo)`: Returns specific vessel by IMO number

### 2. API Endpoint

**Endpoint**: `GET /api/live-vessels/`

**Authentication**: Requires JWT token (Bearer authentication)

**Query Parameters:**
- `limit` (optional): Maximum number of vessels to return (default: 50)
- `imo` (optional): Filter by specific IMO number

**Response Format:**
```json
{
  "count": 5,
  "vessels": [
    {
      "imo": "9123456",
      "name": "ATLANTIC STAR",
      "vessel_type": "Container Ship",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "speed": 15.4,
      "heading": 126,
      "timestamp": "2025-12-29T18:26:42.713792+00:00"
    }
  ]
}
```

### 3. Data Structure

Each vessel record includes:
- **IMO**: International Maritime Organization number
- **Name**: Vessel name
- **Vessel Type**: Type of vessel (Container Ship, Tanker, etc.)
- **Latitude**: Current latitude position
- **Longitude**: Current longitude position
- **Speed**: Speed in knots
- **Heading**: Heading in degrees (0-359)
- **Timestamp**: ISO timestamp of last position update

## Usage Examples

### Basic Request
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/live-vessels/
```

### Limited Results
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:8000/api/live-vessels/?limit=10"
```

### Specific Vessel
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:8000/api/live-vessels/?imo=9123456"
```

## Future Integration with Real AIS APIs

The service is designed for easy integration with real AIS providers:

### MarineTraffic API Integration
```python
# Example configuration in settings.py
AIS_PROVIDER = 'marinetraffic'
MARINETRAFFIC_API_KEY = 'your-api-key-here'

# Service initialization
ais_service = AISDataService(api_key=settings.MARINETRAFFIC_API_KEY)
```

### Supported Providers (Future)
- MarineTraffic API
- VesselFinder API
- AISHub API
- Custom AIS data feeds

## Security & Authentication

- **JWT Required**: All requests require valid JWT authentication
- **Role-Based**: Uses existing permission system
- **Rate Limiting**: Ready for rate limiting implementation
- **API Key Management**: Structured for secure API key handling

## Testing

Run the test script to verify functionality:
```bash
python test_ais_integration.py
```

## Architecture Benefits

1. **Separation of Concerns**: AIS logic isolated in service layer
2. **Easy Testing**: Mock data allows development without API dependencies
3. **Scalable**: Ready for multiple AIS provider integration
4. **Consistent**: Uses existing Django patterns and authentication
5. **Maintainable**: Clear structure for future enhancements

## Error Handling

The API handles various error scenarios:
- Invalid limit parameter
- Service unavailable
- Authentication failures
- Rate limiting (when implemented)

## Performance Considerations

- **Caching**: Ready for Redis/Memcached integration
- **Pagination**: Limit parameter controls response size
- **Async**: Can be enhanced with async/await for better performance
- **Database**: No database queries for live data (external API only)

## Next Steps

1. **Real API Integration**: Connect to MarineTraffic or similar provider
2. **Caching Layer**: Implement Redis caching for frequently requested data
3. **Rate Limiting**: Add rate limiting for API protection
4. **WebSocket Support**: Real-time updates via WebSocket connections
5. **Data Persistence**: Optional vessel position history storage
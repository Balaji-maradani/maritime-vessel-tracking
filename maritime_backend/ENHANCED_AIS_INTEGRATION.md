# Enhanced AIS Data Integration

This document describes the enhanced AIS (Automatic Identification System) data integration for real-time vessel tracking in the maritime analytics platform.

## Overview

The enhanced AIS integration provides:
- **Multi-provider support**: MarineTraffic, AISHub, VesselFinder
- **Real-time vessel tracking** with position, speed, heading, and vessel details
- **Robust error handling** with fallback to mock data
- **Duplicate prevention** using IMO/MMSI identification
- **Comprehensive logging** and monitoring
- **Background job integration** for automated updates

## Architecture

### Core Components

1. **AISDataService** (`core/services/ais_data.py`)
   - Handles API communication with AIS providers
   - Normalizes responses from different providers
   - Provides fallback mock data for development

2. **VesselTrackingService** (`core/services/vessel_tracking.py`)
   - Processes and persists vessel data
   - Handles deduplication and updates
   - Manages data validation and normalization

3. **Enhanced Vessel Model** (`core/models.py`)
   - Added MMSI, speed, and heading fields
   - Maintains backward compatibility

## New Vessel Model Fields

```python
class Vessel(models.Model):
    imo_number = models.CharField(max_length=50, unique=True)  # Existing
    mmsi = models.CharField(max_length=20, null=True, blank=True)  # NEW
    name = models.CharField(max_length=255)  # Existing
    vessel_type = models.CharField(max_length=50)  # Existing
    flag = models.CharField(max_length=50)  # Existing
    cargo_type = models.CharField(max_length=50)  # Existing
    operator = models.CharField(max_length=255)  # Existing
    last_position_lat = models.FloatField(null=True, blank=True)  # Existing
    last_position_lon = models.FloatField(null=True, blank=True)  # Existing
    speed = models.FloatField(null=True, blank=True)  # NEW
    heading = models.IntegerField(null=True, blank=True)  # NEW
    last_update = models.DateTimeField(auto_now=True)  # Existing
```

## AIS Provider Support

### MarineTraffic API
```python
ais_service = AISDataService(api_key='your_key', provider='marinetraffic')
```
- **Endpoint**: `https://services.marinetraffic.com/api/exportvessels/{api_key}/v:3/protocol:json`
- **Features**: Global coverage, high accuracy, commercial grade
- **Rate Limits**: Varies by subscription plan

### AISHub API
```python
ais_service = AISDataService(api_key='your_username', provider='aishub')
```
- **Endpoint**: `http://data.aishub.net/ws.php`
- **Features**: Free tier available, good coverage
- **Authentication**: Username-based

### VesselFinder API
```python
ais_service = AISDataService(api_key='your_token', provider='vesselfinder')
```
- **Endpoint**: `https://api.vesselfinder.com/api/vessels`
- **Features**: Real-time data, vessel details
- **Authentication**: Bearer token

## Configuration

### Django Settings
```python
# settings.py
AIS_API_KEY = 'your-api-key-here'
AIS_PROVIDER = 'marinetraffic'  # or 'aishub', 'vesselfinder'
VESSEL_UPDATE_THRESHOLD_MINUTES = 5  # Minimum time between updates

# Logging configuration
LOGGING = {
    'loggers': {
        'core.services.ais_data': {
            'level': 'INFO',
            'handlers': ['file'],
        },
        'core.services.vessel_tracking': {
            'level': 'INFO',
            'handlers': ['file'],
        },
    },
}
```

## Usage Examples

### Basic Vessel Update
```python
from core.services.vessel_tracking import VesselTrackingService

# Initialize service
tracking_service = VesselTrackingService()

# Fetch and update vessels
summary = tracking_service.fetch_and_update_vessels(limit=100)
print(f"Updated {summary['updated_count']} vessels")
```

### Specific Area Tracking
```python
# Define bounding box (Gulf region)
bbox = {
    'min_lat': 24.0,
    'min_lon': 50.0,
    'max_lat': 27.0,
    'max_lon': 57.0
}

# Fetch vessels in specific area
summary = tracking_service.fetch_and_update_vessels(limit=50, bbox=bbox)
```

### Single Vessel Update
```python
# Update specific vessel by IMO
result = tracking_service.update_vessel_from_ais('9123456')
if result['success']:
    print(f"Vessel {result['action']}: {result['vessel_name']}")
```

## Management Commands

### Update Vessels
```bash
# Basic update
python manage.py update_vessels

# With specific provider and limit
python manage.py update_vessels --provider marinetraffic --limit 200

# Test connection
python manage.py update_vessels --test-connection

# Update specific area
python manage.py update_vessels --bbox "24.0,50.0,27.0,57.0"

# Verbose output
python manage.py update_vessels --verbose
```

### Background Jobs
```bash
# Run all background jobs (includes vessel updates)
python manage.py run_background_jobs

# Run only vessel position updates
python manage.py run_background_jobs --job vessels
```

## API Endpoints

### Enhanced Live Vessels API
```http
GET /api/live-vessels/
GET /api/live-vessels/?limit=50
GET /api/live-vessels/?imo=9123456
```

**Enhanced Response Format:**
```json
{
  "count": 3,
  "data_source": "live",
  "vessels": [
    {
      "imo": "9123456",
      "mmsi": "123456789",
      "name": "ATLANTIC STAR",
      "vessel_type": "Container Ship",
      "flag": "Panama",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "speed": 12.5,
      "heading": 45,
      "timestamp": "2024-01-08T10:30:00Z"
    }
  ]
}
```

### Vessel List API
```http
GET /api/vessels/
```

**Enhanced Response:**
```json
[
  {
    "id": 1,
    "imo_number": "9123456",
    "mmsi": "123456789",
    "name": "ATLANTIC STAR",
    "vessel_type": "Container Ship",
    "flag": "Panama",
    "cargo_type": "Containers",
    "operator": "Atlantic Shipping",
    "last_position_lat": 40.7128,
    "last_position_lon": -74.0060,
    "speed": 12.5,
    "heading": 45,
    "last_update": "2024-01-08T10:30:00Z"
  }
]
```

## Error Handling & Fallbacks

### Automatic Fallbacks
1. **API Failure**: Falls back to mock data
2. **Invalid Data**: Skips problematic records with logging
3. **Network Issues**: Retries with exponential backoff
4. **Rate Limiting**: Respects API limits and queues requests

### Error Logging
```python
# Comprehensive error tracking
logger.error(f"API fetch failed for {provider}: {str(e)}", exc_info=True)
logger.warning(f"Invalid latitude {latitude} for vessel {imo}")
logger.info(f"Vessel {vessel.name} updated successfully")
```

## Data Validation

### Position Validation
- Latitude: -90 to 90 degrees
- Longitude: -180 to 180 degrees
- Speed: 0 to 100 knots (reasonable limits)
- Heading: 0 to 359 degrees (normalized)

### Duplicate Prevention
1. **Primary**: Match by IMO number
2. **Secondary**: Match by MMSI if no IMO
3. **Update Logic**: Update existing records, don't create duplicates

### Data Freshness
- **Update Threshold**: Configurable minimum time between updates
- **Stale Detection**: Identify vessels not updated recently
- **Timestamp Tracking**: Maintain position timestamp and last update

## Monitoring & Health Checks

### Connection Validation
```python
# Test API connectivity
status = ais_service.validate_api_connection()
print(f"Status: {status['connection_status']}")
print(f"Test vessels: {status['test_vessel_count']}")
```

### System Health API
```http
GET /api/system/health/
```

**Response includes AIS status:**
```json
{
  "components": {
    "ais_service": {
      "status": "healthy",
      "sample_data_available": true
    }
  }
}
```

## Production Deployment

### Scheduled Updates
```bash
# Crontab example - update every 15 minutes
*/15 * * * * /path/to/python manage.py update_vessels --limit 500

# Or use background jobs
*/15 * * * * /path/to/python manage.py run_background_jobs --job vessels
```

### Performance Considerations
- **Batch Processing**: Process vessels in batches to avoid memory issues
- **Database Indexing**: Ensure IMO and MMSI fields are indexed
- **API Rate Limits**: Respect provider rate limits
- **Connection Pooling**: Use connection pooling for database operations

### Security
- **API Key Management**: Store API keys securely in environment variables
- **HTTPS Only**: Use HTTPS for all API communications
- **Input Validation**: Validate all incoming data
- **Error Sanitization**: Don't expose sensitive information in error messages

## Troubleshooting

### Common Issues

1. **No API Key**
   ```
   ⚠️ No API key configured for marinetraffic
   ```
   **Solution**: Set `AIS_API_KEY` in Django settings

2. **API Rate Limiting**
   ```
   ERROR: API request failed: 429 Too Many Requests
   ```
   **Solution**: Reduce update frequency or upgrade API plan

3. **Invalid Coordinates**
   ```
   WARNING: Invalid latitude 91.0 for vessel IMO123
   ```
   **Solution**: Data validation automatically handles this

4. **Database Constraints**
   ```
   ERROR: UNIQUE constraint failed: core_vessel.imo_number
   ```
   **Solution**: Duplicate detection prevents this

### Debug Commands
```bash
# Test specific provider
python manage.py update_vessels --provider aishub --test-connection

# Verbose logging
python manage.py update_vessels --verbose --limit 1

# Check vessel data
python manage.py shell -c "from core.models import Vessel; print(Vessel.objects.count())"
```

## Migration Guide

### From Previous Version
1. **Run Migration**: `python manage.py migrate`
2. **Update Existing Data**: `python manage.py update_vessels --limit 100`
3. **Verify Results**: Check vessel records have new fields populated

### Backward Compatibility
- All existing APIs continue to work
- New fields are optional (null=True, blank=True)
- Legacy functions maintained with deprecation warnings

This enhanced AIS integration provides a robust, scalable solution for real-time vessel tracking with comprehensive error handling and multi-provider support.
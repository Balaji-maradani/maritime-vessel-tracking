# Maritime Analytics Background Jobs System

This document describes the background job system implemented for the maritime analytics platform to improve reliability and ensure data availability.

## Overview

The background job system provides:
- **Periodic data updates** for port congestion and vessel positions
- **Automated safety event detection** for storms and piracy risks
- **Comprehensive error handling** with fallback data
- **System health monitoring** and logging
- **API endpoints** for manual job execution and health checks

## Components

### 1. Background Job Service (`core/services/background_jobs.py`)

Main service class that handles:
- **Port Congestion Updates**: Simulates fetching real-time port data
- **Safety Events Updates**: Runs event detection for storms, piracy, and congestion
- **Vessel Position Updates**: Updates vessel locations from AIS data
- **Fallback Data Management**: Ensures minimum data availability

### 2. Management Commands

#### Run Background Jobs
```bash
# Run all background jobs
python manage.py run_background_jobs

# Run specific job types
python manage.py run_background_jobs --job ports
python manage.py run_background_jobs --job safety
python manage.py run_background_jobs --job vessels

# Verbose output
python manage.py run_background_jobs --verbose
```

#### Ensure Fallback Data
```bash
# Ensure minimum data exists
python manage.py ensure_fallback_data

# Force recreation of fallback data
python manage.py ensure_fallback_data --force
```

#### Event Checks
```bash
# Run event detection
python manage.py check_events

# Dry run mode (no actual changes)
python manage.py check_events --dry-run
```

### 3. API Endpoints

#### Background Jobs API
```http
POST /api/jobs/run/
POST /api/jobs/run/?job=ports
POST /api/jobs/run/?job=safety
POST /api/jobs/run/?job=vessels
```
*Requires ADMIN role*

#### System Health Check
```http
GET /api/system/health/
```
*Returns system status and component health*

#### Event Checks
```http
POST /api/events/check/
```
*Manually trigger event detection (ADMIN only)*

## Enhanced API Reliability

### Port Congestion API (`/api/ports/congestion/`)
- **Fallback Data**: Returns static data if database is empty
- **Error Handling**: Graceful degradation with fallback response
- **Data Validation**: Ensures minimum data availability

### Live Vessels API (`/api/live-vessels/`)
- **Multiple Data Sources**: AIS API → Database → Static fallback
- **Error Recovery**: Automatic fallback on AIS service failure
- **Response Metadata**: Indicates data source (live/fallback/emergency)

## Error Handling & Logging

### Logging Levels
- **INFO**: Normal operations and job completions
- **WARNING**: Non-critical issues (API failures with fallback)
- **ERROR**: Critical errors that need attention
- **DEBUG**: Detailed operation information

### Error Recovery Strategies
1. **API Failures**: Automatic fallback to cached/static data
2. **Database Issues**: Return emergency fallback data
3. **Partial Failures**: Continue processing other items
4. **Critical Errors**: Log and return meaningful error responses

## Fallback Data System

### Port Data Fallback
When port data is unavailable:
1. Check database for existing data
2. Create minimum viable dataset if empty
3. Return static fallback data as last resort

### Vessel Data Fallback
When AIS service fails:
1. Use database vessel positions
2. Return static vessel data
3. Include metadata about data freshness

### Safety Data Fallback
When external safety APIs fail:
1. Use cached safety zone data
2. Generate mock safety events for testing
3. Maintain notification functionality

## Production Deployment

### Scheduled Jobs
Set up cron jobs or task scheduler:

```bash
# Every 15 minutes - update vessel positions
*/15 * * * * /path/to/python manage.py run_background_jobs --job vessels

# Every 30 minutes - update port congestion
*/30 * * * * /path/to/python manage.py run_background_jobs --job ports

# Every hour - check safety events
0 * * * * /path/to/python manage.py run_background_jobs --job safety

# Daily - full system check
0 2 * * * /path/to/python manage.py run_background_jobs --verbose
```

### Celery Integration (Optional)
For production environments, consider integrating with Celery:

```python
# In settings.py
CELERY_BEAT_SCHEDULE = {
    'update-vessel-positions': {
        'task': 'core.tasks.update_vessel_positions',
        'schedule': crontab(minute='*/15'),
    },
    'update-port-congestion': {
        'task': 'core.tasks.update_port_congestion',
        'schedule': crontab(minute='*/30'),
    },
    'check-safety-events': {
        'task': 'core.tasks.check_safety_events',
        'schedule': crontab(minute=0),
    },
}
```

### Environment Configuration

```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'maritime_jobs.log',
        },
    },
    'loggers': {
        'core.services.background_jobs': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# External API configuration
NOAA_WEATHER_URL = 'https://api.weather.gov/alerts'
NOAA_API_KEY = 'your-api-key'
AIS_API_URL = 'https://api.aisstream.io'
AIS_API_KEY = 'your-ais-key'
```

## Monitoring & Alerts

### Health Check Response
```json
{
  "timestamp": "2024-01-07T10:30:00Z",
  "overall_status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "ports": 25,
      "vessels": 150,
      "events": 1200,
      "notifications": 450
    },
    "ais_service": {
      "status": "healthy",
      "sample_data_available": true
    },
    "recent_activity": {
      "status": "healthy",
      "events_24h": 45,
      "notifications_24h": 120
    }
  }
}
```

### Job Execution Summary
```json
{
  "started_at": "2024-01-07T10:30:00Z",
  "completed_at": "2024-01-07T10:32:15Z",
  "duration_seconds": 135.2,
  "total_success": true,
  "jobs": {
    "port_congestion": {
      "ports_updated": 25,
      "errors_count": 0,
      "success": true
    },
    "safety_events": {
      "total_events_created": 3,
      "total_notifications_created": 12,
      "success": true
    },
    "vessel_positions": {
      "vessels_updated": 142,
      "errors_count": 1,
      "success": true
    }
  }
}
```

## Testing

### Unit Tests
```bash
python manage.py test core.tests.test_background_jobs
```

### Manual Testing
```bash
# Test individual components
python manage.py run_background_jobs --job ports --verbose
python manage.py ensure_fallback_data
curl -X GET http://localhost:8000/api/system/health/
```

### Load Testing
Monitor performance under load:
- API response times with fallback data
- Database query performance
- Memory usage during bulk operations

## Troubleshooting

### Common Issues

1. **Migration Errors**: Ensure all migrations are applied
2. **API Timeouts**: Check external service availability
3. **Database Locks**: Monitor concurrent job execution
4. **Memory Usage**: Monitor during large data updates

### Debug Commands
```bash
# Check system status
python manage.py run_background_jobs --job all --verbose

# Verify fallback data
python manage.py ensure_fallback_data --force

# Test API endpoints
curl -X GET "http://localhost:8000/api/system/health/"
curl -X GET "http://localhost:8000/api/ports/congestion/"
```

This background job system ensures the maritime analytics platform remains reliable and responsive even when external services are unavailable.
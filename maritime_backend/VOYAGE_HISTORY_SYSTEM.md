# Voyage History and Replay System

## Overview

The Voyage History and Replay System provides comprehensive tracking, storage, and visualization of vessel movements throughout their voyages. This system enables historical analysis, compliance reporting, and interactive replay of vessel routes.

## Features

### 1. Historical Position Storage
- **Optimized Storage**: Efficient database schema with proper indexing
- **Automatic Recording**: Seamless integration with live AIS tracking
- **Duplicate Prevention**: Prevents duplicate position records
- **Source Tracking**: Records data source (AIS, GPS, Manual, etc.)
- **Accuracy Metadata**: Stores position accuracy information

### 2. Voyage Association
- **Automatic Grouping**: Positions automatically associated with active voyages
- **Smart Detection**: Auto-starts voyages based on position data
- **Status Tracking**: Monitors voyage progression and completion
- **Route Reconstruction**: Rebuilds complete voyage routes from positions

### 3. Replay Functionality
- **Interactive Visualization**: Generate replay data for frontend mapping
- **Speed Control**: Configurable replay speed multipliers
- **Gap Interpolation**: Smart interpolation for missing position data
- **Timing Metadata**: Precise timing information for smooth playback
- **Distance Calculations**: Accurate distance and speed calculations

### 4. Audit and Compliance
- **Comprehensive Logging**: All actions logged for regulatory compliance
- **User Tracking**: Records user actions and IP addresses
- **Compliance Categories**: Organized by regulatory requirements (SOLAS, MARPOL, etc.)
- **Data Retention**: Configurable retention policies
- **Access Control**: Role-based access to sensitive data

### 5. Storage Optimization
- **Efficient Indexing**: Optimized database indexes for fast queries
- **Data Compression**: Intelligent storage of position data
- **Cleanup Automation**: Automated cleanup of old data
- **Performance Monitoring**: Query optimization and performance tracking

## Database Schema

### VesselPosition Model
```python
class VesselPosition(models.Model):
    vessel = models.ForeignKey(Vessel, related_name='positions')
    voyage = models.ForeignKey(Voyage, related_name='positions', null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(null=True)
    heading = models.IntegerField(null=True)
    timestamp = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=50, default='AIS')
    accuracy = models.FloatField(null=True)
    is_interpolated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

### VoyageAuditLog Model
```python
class VoyageAuditLog(models.Model):
    voyage = models.ForeignKey(Voyage, related_name='audit_logs', null=True)
    vessel = models.ForeignKey(Vessel, related_name='audit_logs')
    user = models.ForeignKey(User, related_name='audit_logs', null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(null=True)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    compliance_category = models.CharField(max_length=100, null=True)
    retention_date = models.DateTimeField(null=True)
```

## API Endpoints

### 1. Vessel History
```
GET /api/vessels/{vessel_id}/history/
```
**Parameters:**
- `start_date`: Start date (ISO format)
- `end_date`: End date (ISO format)
- `limit`: Maximum positions to return (default: 1000)

**Response:**
```json
{
  "vessel": {
    "id": 123,
    "name": "Ocean Explorer",
    "imo_number": "IMO9234567"
  },
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "positions": [...],
  "voyages": {...},
  "total_positions": 1500,
  "has_more": false
}
```

### 2. Voyage Route
```
GET /api/voyages/{voyage_id}/route/
```
**Parameters:**
- `include_interpolated`: Include interpolated positions (default: false)

**Response:**
```json
{
  "voyage": {
    "id": 456,
    "vessel_name": "Ocean Explorer",
    "port_from": "Dubai",
    "port_to": "Singapore",
    "status": "COMPLETED"
  },
  "route": [...],
  "total_positions": 250
}
```

### 3. Voyage Replay
```
POST /api/voyages/{voyage_id}/replay/
```
**Request Body:**
```json
{
  "speed_multiplier": 2.0,
  "interpolate_gaps": true
}
```

**Response:**
```json
{
  "voyage": {...},
  "replay_settings": {
    "speed_multiplier": 2.0,
    "interpolate_gaps": true
  },
  "metadata": {
    "total_positions": 250,
    "actual_duration_seconds": 86400,
    "replay_duration_seconds": 43200,
    "total_distance_nm": 1250.5,
    "average_speed": 15.2
  },
  "positions": [...]
}
```

### 4. Voyage Statistics
```
GET /api/voyages/{voyage_id}/statistics/
```

**Response:**
```json
{
  "voyage_id": 456,
  "vessel_name": "Ocean Explorer",
  "route": "Dubai → Singapore",
  "status": "COMPLETED",
  "statistics": {
    "total_positions": 250,
    "total_distance_nm": 1250.5,
    "duration_hours": 72.5,
    "average_speed_knots": 15.2,
    "max_speed_knots": 22.1,
    "min_speed_knots": 0.0
  }
}
```

### 5. Record Position
```
POST /api/positions/record/
```
**Request Body:**
```json
{
  "vessel_id": 123,
  "latitude": 25.2048,
  "longitude": 55.2708,
  "timestamp": "2024-01-08T12:00:00Z",
  "speed": 12.5,
  "heading": 45,
  "source": "MANUAL",
  "accuracy": 10.0
}
```

### 6. Audit Logs
```
GET /api/voyages/{voyage_id}/audit-logs/
```
**Parameters:**
- `limit`: Maximum logs to return (default: 100)
- `action`: Filter by action type

## Service Classes

### VoyageHistoryService
Main service class providing:
- Position recording and storage
- Voyage association logic
- Route reconstruction
- Replay data generation
- Statistics calculation
- Data cleanup operations

### VoyageReplayService
Specialized service for replay functionality:
- Replay session management
- Frame-by-frame data access
- Interpolation algorithms
- Timing calculations

## Integration Points

### 1. AIS Data Integration
The system automatically integrates with the existing AIS tracking system:

```python
# In VesselTrackingService._upsert_vessel()
history_service.record_position(
    vessel=vessel,
    latitude=position_data['latitude'],
    longitude=position_data['longitude'],
    timestamp=position_timestamp,
    speed=position_data.get('speed'),
    heading=position_data.get('heading'),
    source='AIS'
)
```

### 2. Background Jobs
Position recording is integrated with background job processing for automated data collection.

### 3. Notification System
Voyage events trigger notifications through the existing notification system.

## Configuration

### Settings
```python
# Position data retention (days)
POSITION_RETENTION_DAYS = 365

# Audit log retention (days) 
AUDIT_RETENTION_DAYS = 2555  # 7 years

# Position interpolation threshold (minutes)
POSITION_INTERPOLATION_THRESHOLD = 30
```

### Database Indexes
The system uses optimized database indexes for performance:
- `(vessel, timestamp)` - Fast vessel history queries
- `(voyage, timestamp)` - Fast voyage route queries
- `(timestamp)` - Time-based queries
- `(vessel, voyage)` - Voyage association queries

## Management Commands

### Test System
```bash
python manage.py test_voyage_history --verbose
```

### Create Sample Data
```bash
python manage.py test_voyage_history --create-sample-data
```

### Test Replay
```bash
python manage.py test_voyage_history --test-replay
```

### Data Cleanup
```bash
python manage.py test_voyage_history --cleanup --dry-run
```

## Performance Considerations

### 1. Storage Optimization
- Positions older than retention period are automatically cleaned up
- Efficient indexing reduces query time
- Batch operations for bulk data processing

### 2. Query Optimization
- Paginated results for large datasets
- Selective field loading
- Optimized database queries with proper joins

### 3. Memory Management
- Streaming data processing for large voyages
- Efficient serialization
- Garbage collection optimization

## Compliance Features

### 1. Audit Trail
- Complete audit trail of all position data access
- User action tracking with IP addresses
- Compliance category classification

### 2. Data Retention
- Configurable retention policies
- Automated cleanup processes
- Compliance with maritime regulations

### 3. Access Control
- Role-based access to historical data
- Audit log access restricted to admins/analysts
- Position recording requires operator+ permissions

## Frontend Integration

### 1. Map Visualization
The system provides data structures optimized for map visualization:
- GeoJSON-compatible position arrays
- Timing information for animated playback
- Interpolated positions for smooth routes

### 2. Replay Controls
Frontend can implement:
- Play/pause controls
- Speed adjustment
- Timeline scrubbing
- Route highlighting

### 3. Statistics Dashboard
Historical data enables:
- Voyage performance metrics
- Route efficiency analysis
- Compliance reporting
- Trend analysis

## Error Handling

### 1. Position Recording
- Duplicate position prevention
- Invalid coordinate validation
- Timestamp validation
- Source verification

### 2. Data Integrity
- Transaction-based operations
- Rollback on errors
- Data validation at multiple levels
- Graceful degradation

### 3. Performance Monitoring
- Query performance tracking
- Storage usage monitoring
- Error rate monitoring
- Alert generation

## Future Enhancements

### 1. Advanced Analytics
- Route optimization suggestions
- Fuel efficiency analysis
- Weather correlation
- Performance benchmarking

### 2. Real-time Features
- Live position streaming
- Real-time replay
- WebSocket integration
- Push notifications

### 3. Machine Learning
- Route prediction
- Anomaly detection
- Performance optimization
- Predictive maintenance

## Testing

The system includes comprehensive testing:
- Unit tests for all service methods
- Integration tests for API endpoints
- Performance tests for large datasets
- Compliance tests for audit requirements

Run tests with:
```bash
python manage.py test core.tests.test_voyage_history
python manage.py test_voyage_history --verbose
```

## Monitoring

### 1. Metrics
- Position recording rate
- Storage usage
- Query performance
- Error rates

### 2. Alerts
- Storage threshold warnings
- Performance degradation alerts
- Data integrity issues
- Compliance violations

### 3. Reporting
- Daily position summaries
- Weekly voyage reports
- Monthly compliance reports
- Annual data retention reports
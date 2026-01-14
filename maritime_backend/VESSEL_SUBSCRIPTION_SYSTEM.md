# Vessel Subscription & Enhanced Notification System

This document describes the enhanced notification system with vessel subscription support for the maritime analytics platform.

## Overview

The enhanced notification system provides:
- **User-specific vessel subscriptions** with granular notification preferences
- **Event-driven notifications** for storm zones, piracy risks, and congestion
- **Flexible subscription management** via REST APIs
- **Backward compatibility** with existing notification system
- **JWT-protected endpoints** for secure access

## Architecture

### Core Components

1. **VesselSubscription Model** - Tracks user subscriptions to specific vessels
2. **Enhanced NotificationService** - Handles subscription-based notifications
3. **REST API Endpoints** - Manage subscriptions and retrieve notifications
4. **Event Triggers** - Automatic notification generation for safety events

## VesselSubscription Model

```python
class VesselSubscription(models.Model):
    user = models.ForeignKey(User, related_name='vessel_subscriptions')
    vessel = models.ForeignKey(Vessel, related_name='subscribers')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPE_CHOICES)
    notify_storm_zones = models.BooleanField(default=True)
    notify_piracy_zones = models.BooleanField(default=True)
    notify_congestion = models.BooleanField(default=True)
    notify_position_updates = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'vessel')
```

### Subscription Types

- **ALL_EVENTS**: Receive all notifications for the vessel
- **SAFETY_ONLY**: Only safety-related events (storms, piracy, incidents)
- **POSITION_UPDATES**: Only position and movement updates
- **CUSTOM**: Custom notification preferences based on individual flags

### Notification Preferences

Each subscription allows granular control over notification types:
- **Storm Zones**: Notifications when vessel enters severe weather areas
- **Piracy Zones**: Alerts for high-risk piracy areas
- **Congestion**: Warnings about port congestion and delays
- **Position Updates**: Regular position and movement notifications

## API Endpoints

### 1. Subscribe to Vessel
```http
POST /api/subscribe-vessel/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
    "vessel_id": 123,
    "notify_storm_zones": true,
    "notify_piracy_zones": true,
    "notify_congestion": true,
    "notify_position_updates": false,
    "subscription_type": "ALL_EVENTS"
}
```

**Response:**
```json
{
    "message": "Vessel subscription created successfully",
    "subscription_id": 456,
    "vessel_name": "ATLANTIC STAR",
    "vessel_imo": "9123456",
    "action": "created"
}
```

### 2. List User Subscriptions
```http
GET /api/vessel-subscriptions/
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
    {
        "id": 456,
        "vessel": 123,
        "vessel_name": "ATLANTIC STAR",
        "vessel_imo": "9123456",
        "vessel_type": "Container Ship",
        "vessel_flag": "Panama",
        "subscription_type": "ALL_EVENTS",
        "notify_storm_zones": true,
        "notify_piracy_zones": true,
        "notify_congestion": true,
        "notify_position_updates": false,
        "is_active": true,
        "created_at": "2024-01-08T10:30:00Z"
    }
]
```

### 3. Update Subscription
```http
PUT /api/vessel-subscriptions/456/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
    "notify_storm_zones": false,
    "notify_piracy_zones": true,
    "notify_congestion": true,
    "subscription_type": "SAFETY_ONLY"
}
```

### 4. Unsubscribe from Vessel
```http
DELETE /api/unsubscribe-vessel/123/
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "message": "Successfully unsubscribed from ATLANTIC STAR"
}
```

### 5. Get Notifications (Enhanced)
```http
GET /api/notifications/
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
    {
        "id": 789,
        "vessel": 123,
        "vessel_name": "ATLANTIC STAR",
        "event": 456,
        "event_type": "STORM_ENTRY",
        "message": "🌩️ Your subscribed vessel ATLANTIC STAR has entered a storm zone at Storm Zone near 40.7128, -74.0060. Monitor weather conditions closely.",
        "notification_type": "EVENT_ALERT",
        "is_read": false,
        "timestamp": "2024-01-08T10:30:00Z"
    }
]
```

## Event-Driven Notifications

### Automatic Triggers

The system automatically generates notifications when:

1. **Storm Zone Entry** (`STORM_ENTRY`)
   - Vessel enters severe weather area
   - Triggered by weather monitoring systems
   - Includes severity and wind speed information

2. **Piracy Risk Zone Entry** (`PIRACY_RISK`)
   - Vessel enters high-risk piracy area
   - Based on maritime security databases
   - Includes risk level and recent incident data

3. **High Port Congestion** (`HIGH_CONGESTION`)
   - Vessel approaches congested port
   - Based on port congestion scores ≥ 7.0
   - Includes expected delay information

### Notification Flow

```
Event Occurs → Event Created → Subscription Check → Personalized Notifications → Database Storage
```

1. **Event Detection**: System detects safety event (storm, piracy, congestion)
2. **Event Creation**: Creates Event record with details
3. **Subscription Lookup**: Finds users subscribed to affected vessel
4. **Preference Filtering**: Checks user notification preferences
5. **Message Generation**: Creates personalized notification messages
6. **Notification Storage**: Stores notifications in database
7. **Delivery**: Notifications available via API

### Enhanced NotificationService

```python
# Automatic subscription-based notifications
notifications_count = NotificationService.notify_users_for_event(event)

# The service now:
# 1. Checks vessel subscriptions
# 2. Filters by user preferences
# 3. Generates personalized messages
# 4. Creates notifications for both subscribers and role-based users
```

## Usage Examples

### Python/Django Usage

```python
from core.models import VesselSubscription, Vessel
from django.contrib.auth import get_user_model

User = get_user_model()

# Create subscription
user = User.objects.get(username='captain_smith')
vessel = Vessel.objects.get(imo_number='9123456')

subscription = VesselSubscription.objects.create(
    user=user,
    vessel=vessel,
    subscription_type='SAFETY_ONLY',
    notify_storm_zones=True,
    notify_piracy_zones=True,
    notify_congestion=False
)

# Check user's subscriptions
user_subscriptions = VesselSubscription.objects.filter(
    user=user,
    is_active=True
)

# Get vessel subscribers
vessel_subscribers = VesselSubscription.objects.filter(
    vessel=vessel,
    is_active=True,
    notify_storm_zones=True
)
```

### JavaScript/Frontend Usage

```javascript
// Subscribe to vessel
const subscribeToVessel = async (vesselId, preferences) => {
    const response = await fetch('/api/subscribe-vessel/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            vessel_id: vesselId,
            notify_storm_zones: preferences.storms,
            notify_piracy_zones: preferences.piracy,
            notify_congestion: preferences.congestion
        })
    });
    
    return response.json();
};

// Get user subscriptions
const getUserSubscriptions = async () => {
    const response = await fetch('/api/vessel-subscriptions/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    return response.json();
};

// Get notifications
const getNotifications = async () => {
    const response = await fetch('/api/notifications/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    return response.json();
};
```

## Management Commands

### Test Subscription System
```bash
# Create test data
python manage.py test_vessel_subscriptions --create-test-data

# List current subscriptions
python manage.py test_vessel_subscriptions --list-subscriptions

# Trigger test events
python manage.py test_vessel_subscriptions --trigger-events
```

### Update Vessels (includes subscription notifications)
```bash
# Update vessel positions and trigger notifications
python manage.py update_vessels --limit 100

# Run background jobs (includes notification processing)
python manage.py run_background_jobs
```

## Database Schema

### Migration Applied
- **Migration**: `0007_add_vessel_subscription_model`
- **Safe Migration**: Uses `unique_together` constraint
- **Backward Compatible**: Existing notification system unchanged

### Indexes
The system automatically creates indexes for:
- `(user, vessel)` - Unique constraint for subscriptions
- `user` - Foreign key index for user lookups
- `vessel` - Foreign key index for vessel lookups
- `is_active` - Boolean index for active subscriptions

## Security & Authentication

### JWT Protection
All subscription endpoints require valid JWT authentication:
```python
permission_classes = [IsAuthenticated]
```

### User Isolation
- Users can only manage their own subscriptions
- Notifications are filtered by authenticated user
- No cross-user data access

### Input Validation
- Vessel existence validation
- Subscription uniqueness enforcement
- Boolean preference validation
- Enum choice validation for subscription types

## Performance Considerations

### Optimizations
- **Bulk Notification Creation**: Uses `bulk_create()` for efficiency
- **Select Related**: Optimized queries with `select_related()`
- **Database Indexes**: Proper indexing for fast lookups
- **Subscription Filtering**: Efficient preference-based filtering

### Scalability
- **Async Processing**: Ready for background job processing
- **Batch Operations**: Supports bulk subscription management
- **Caching**: Can be enhanced with Redis caching
- **Database Partitioning**: Notifications can be partitioned by date

## Monitoring & Analytics

### Subscription Metrics
```python
# Total active subscriptions
active_subs = VesselSubscription.objects.filter(is_active=True).count()

# Most subscribed vessels
popular_vessels = Vessel.objects.annotate(
    subscriber_count=Count('subscribers', filter=Q(subscribers__is_active=True))
).order_by('-subscriber_count')

# Notification delivery stats
notification_stats = Notification.objects.aggregate(
    total=Count('id'),
    unread=Count('id', filter=Q(is_read=False)),
    by_type=Count('notification_type')
)
```

### Health Checks
- Subscription creation/update success rates
- Notification delivery metrics
- Event processing latency
- API endpoint response times

## Error Handling

### Common Scenarios
1. **Duplicate Subscription**: Updates existing instead of creating new
2. **Invalid Vessel**: Returns 404 with clear error message
3. **Authentication Failure**: Returns 401 with token refresh guidance
4. **Database Errors**: Graceful degradation with error logging

### Logging
```python
logger.info(f"Created subscription: {user.username} -> {vessel.name}")
logger.warning(f"Duplicate subscription attempt: {user.username} -> {vessel.name}")
logger.error(f"Failed to create notification: {str(e)}", exc_info=True)
```

## Future Enhancements

### Planned Features
- **Push Notifications**: Mobile and web push notification support
- **Email Notifications**: Optional email delivery
- **Notification Scheduling**: Time-based notification preferences
- **Bulk Subscription Management**: Subscribe to multiple vessels
- **Notification Templates**: Customizable message templates
- **Analytics Dashboard**: Subscription and notification analytics

### Integration Points
- **WebSocket Support**: Real-time notification delivery
- **External APIs**: Integration with maritime alert services
- **Mobile Apps**: Native mobile notification support
- **Third-party Services**: Slack, Teams, SMS integration

This enhanced notification system provides a robust, scalable foundation for vessel-specific notifications while maintaining full backward compatibility with the existing system.
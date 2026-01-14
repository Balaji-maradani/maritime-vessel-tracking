from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    dashboard_api,
    VesselListView,
    RegisterView,
    me_api,
    PortCongestionView,
    SafetyAlertsView,
    UserNotificationListView,
    live_vessels_api,
    trigger_event_checks_api,
    run_background_jobs_api,
    system_health_api,
    VesselSubscriptionView,
    VesselSubscriptionListView,
    VesselSubscriptionDetailView,
    subscribe_vessel_api,
    unsubscribe_vessel_api,
    port_congestion_analytics_api,
    ports_dashboard_api,
    refresh_port_analytics_api,
    vessel_history_api,
    voyage_route_api,
    voyage_replay_api,
    voyage_statistics_api,
    record_vessel_position_api,
    voyage_audit_logs_api,
)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', me_api, name='me'),

    # Vessels & ports
    path('vessels/', VesselListView.as_view(), name='vessels'),
    path('live-vessels/', live_vessels_api, name='live_vessels'),
    path('ports/congestion/', PortCongestionView.as_view(), name='port_congestion'),
    path('port-congestion/', port_congestion_analytics_api, name='port_congestion_analytics'),
    path('ports/dashboard/', ports_dashboard_api, name='ports_dashboard'),
    path('ports/refresh/', refresh_port_analytics_api, name='refresh_port_analytics'),

    # Alerts & notifications
    path('notifications/', UserNotificationListView.as_view(), name='notifications'),
    path('alerts/safety/', SafetyAlertsView.as_view(), name='safety_alerts'),
    path('events/check/', trigger_event_checks_api, name='trigger_event_checks'),

    # Vessel subscriptions
    path('subscribe-vessel/', subscribe_vessel_api, name='subscribe_vessel'),
    path('unsubscribe-vessel/<int:vessel_id>/', unsubscribe_vessel_api, name='unsubscribe_vessel'),
    path('vessel-subscriptions/', VesselSubscriptionListView.as_view(), name='vessel_subscriptions_list'),
    path('vessel-subscriptions/create/', VesselSubscriptionView.as_view(), name='vessel_subscriptions_create'),
    path('vessel-subscriptions/<int:pk>/', VesselSubscriptionDetailView.as_view(), name='vessel_subscriptions_detail'),

    # Voyage history and replay
    path('vessels/<int:vessel_id>/history/', vessel_history_api, name='vessel_history'),
    path('voyages/<int:voyage_id>/route/', voyage_route_api, name='voyage_route'),
    path('voyages/<int:voyage_id>/replay/', voyage_replay_api, name='voyage_replay'),
    path('voyages/<int:voyage_id>/statistics/', voyage_statistics_api, name='voyage_statistics'),
    path('voyages/<int:voyage_id>/audit-logs/', voyage_audit_logs_api, name='voyage_audit_logs'),
    path('positions/record/', record_vessel_position_api, name='record_position'),

    # Background jobs & system health
    path('jobs/run/', run_background_jobs_api, name='run_background_jobs'),
    path('system/health/', system_health_api, name='system_health'),

    # Other API endpoints
    path('dashboard/', dashboard_api, name='dashboard'),
]

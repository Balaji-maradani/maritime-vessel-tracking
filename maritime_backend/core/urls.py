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
    SubscribeVesselAlertView,
    PortCongestionView,
    SafetyAlertsView,
    UserNotificationListView,
    live_vessels_api,
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

    # Alerts & notifications
    path('alerts/subscribe/', SubscribeVesselAlertView.as_view(), name='subscribe_alert'),
    path('alerts/safety/', SafetyAlertsView.as_view(), name='safety_alerts'),
    path('notifications/', UserNotificationListView.as_view(), name='notifications'),

    # Other API endpoints
    path('dashboard/', dashboard_api, name='dashboard'),
]

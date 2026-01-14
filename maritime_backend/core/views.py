from django.http import HttpResponse
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny

import logging

logger = logging.getLogger(__name__)

from .models import Vessel, Port, Voyage, User, Event, Notification, VesselSubscription
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    VesselSerializer,
    NotificationCreateSerializer,
    PortCongestionSerializer,
    EventSerializer,
    NotificationSerializer,
    LiveVesselSerializer,
    VesselSubscriptionCreateSerializer,
    VesselSubscriptionListSerializer,
    VesselSubscriptionSerializer,
)
from .permissions import IsAnalyst, IsOperator
from .services.ais_data import AISDataService
from .services.notification_service import run_all_event_checks
from .services.background_jobs import BackgroundJobService, FallbackDataService


# -------------------------------------------------
# HOME
# -------------------------------------------------
def home(request):
    return HttpResponse("Maritime Backend API is running 🚢")


# -------------------------------------------------
# DASHBOARD API (Analyst + Admin)
# -------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAnalyst])
def dashboard_api(request):
    data = {
        "total_vessels": Vessel.objects.count(),
        "total_ports": Port.objects.count(),
        "total_voyages": Voyage.objects.count(),
    }
    return Response(data)


class VesselListView(generics.ListAPIView):
    """
    Lists vessels with optional filtering by type, flag, and cargo type.
    Requires JWT authentication.
    """

    serializer_class = VesselSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Vessel.objects.all()
        vessel_type = self.request.query_params.get("type")
        flag = self.request.query_params.get("flag")
        cargo = self.request.query_params.get("cargo")

        if vessel_type:
            queryset = queryset.filter(vessel_type__iexact=vessel_type)
        if flag:
            queryset = queryset.filter(flag__iexact=flag)
        if cargo:
            queryset = queryset.filter(cargo_type__iexact=cargo)

        return queryset.order_by("name")


class PortCongestionView(generics.ListAPIView):
    """
    Returns congestion and average wait time metrics for all ports.
    Includes fallback data handling and comprehensive error logging.
    Requires JWT authentication.
    """

    serializer_class = PortCongestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            # Ensure we have fallback data available
            FallbackDataService.ensure_minimum_port_data()
            
            queryset = Port.objects.all().order_by("-congestion_score")
            
            if not queryset.exists():
                logger.warning("No port data available even after fallback data creation")
            
            return queryset
            
        except Exception as e:
            logger.error(f"Error in PortCongestionView.get_queryset: {str(e)}", exc_info=True)
            # Return empty queryset but let the view handle it gracefully
            return Port.objects.none()
    
    def list(self, request, *args, **kwargs):
        """
        Override list method to provide fallback response if needed.
        """
        try:
            response = super().list(request, *args, **kwargs)
            
            # If we have no data, provide fallback
            if not response.data:
                logger.warning("No port data available, providing fallback data")
                fallback_data = FallbackDataService.get_fallback_port_data()
                return Response(fallback_data, status=status.HTTP_200_OK)
            
            return response
            
        except Exception as e:
            logger.error(f"Critical error in PortCongestionView: {str(e)}", exc_info=True)
            
            # Provide fallback data in case of any error
            fallback_data = FallbackDataService.get_fallback_port_data()
            return Response(
                fallback_data,
                status=status.HTTP_200_OK,
                headers={'X-Fallback-Data': 'true'}
            )

# -------------------------------------------------
# USER REGISTRATION
# -------------------------------------------------
class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    Allows unauthenticated users to create new accounts.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "User registered successfully",
                "user": UserProfileSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )


# -------------------------------------------------
# USER PROFILE API
# -------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_api(request):
    """
    Returns the authenticated user's profile information.
    Requires JWT authentication.
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


# -------------------------------------------------
# VESSEL SUBSCRIPTION MANAGEMENT
# -------------------------------------------------
class VesselSubscriptionView(generics.CreateAPIView):
    """
    Create or update vessel subscription for the authenticated user.
    Allows users to subscribe to specific vessels for notifications.
    """
    serializer_class = VesselSubscriptionCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """
        Create or update vessel subscription.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()
            
            # Return detailed subscription info
            response_serializer = VesselSubscriptionSerializer(subscription)
            
            return Response({
                'message': 'Vessel subscription created/updated successfully',
                'subscription': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating vessel subscription: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to create vessel subscription'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VesselSubscriptionListView(generics.ListAPIView):
    """
    List all vessel subscriptions for the authenticated user.
    """
    serializer_class = VesselSubscriptionListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return VesselSubscription.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('vessel').order_by('-created_at')


class VesselSubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific vessel subscription.
    """
    serializer_class = VesselSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return VesselSubscription.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """
        Unsubscribe from vessel (soft delete by setting is_active=False).
        """
        try:
            subscription = self.get_object()
            subscription.is_active = False
            subscription.save()
            
            return Response({
                'message': f'Successfully unsubscribed from {subscription.vessel.name}'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error unsubscribing from vessel: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to unsubscribe from vessel'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_vessel_api(request):
    """
    Simple API endpoint to subscribe to a vessel.
    
    POST data:
    {
        "vessel_id": 123,
        "notify_storm_zones": true,
        "notify_piracy_zones": true,
        "notify_congestion": true
    }
    """
    try:
        vessel_id = request.data.get('vessel_id')
        if not vessel_id:
            return Response(
                {'error': 'vessel_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vessel = Vessel.objects.get(id=vessel_id)
        except Vessel.DoesNotExist:
            return Response(
                {'error': 'Vessel not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create or update subscription
        subscription, created = VesselSubscription.objects.update_or_create(
            user=request.user,
            vessel=vessel,
            defaults={
                'notify_storm_zones': request.data.get('notify_storm_zones', True),
                'notify_piracy_zones': request.data.get('notify_piracy_zones', True),
                'notify_congestion': request.data.get('notify_congestion', True),
                'notify_position_updates': request.data.get('notify_position_updates', False),
                'subscription_type': request.data.get('subscription_type', 'ALL_EVENTS'),
                'is_active': True,
            }
        )
        
        action = 'created' if created else 'updated'
        return Response({
            'message': f'Vessel subscription {action} successfully',
            'subscription_id': subscription.id,
            'vessel_name': vessel.name,
            'vessel_imo': vessel.imo_number,
            'action': action
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in subscribe_vessel_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to process vessel subscription'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unsubscribe_vessel_api(request, vessel_id):
    """
    Unsubscribe from a vessel.
    
    DELETE /api/unsubscribe-vessel/{vessel_id}/
    """
    try:
        subscription = VesselSubscription.objects.get(
            user=request.user,
            vessel_id=vessel_id,
            is_active=True
        )
        
        subscription.is_active = False
        subscription.save()
        
        return Response({
            'message': f'Successfully unsubscribed from {subscription.vessel.name}'
        }, status=status.HTTP_200_OK)
        
    except VesselSubscription.DoesNotExist:
        return Response(
            {'error': 'Subscription not found or already inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in unsubscribe_vessel_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to unsubscribe from vessel'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SafetyAlertsView(generics.ListAPIView):
    """
    List recent safety-related events (e.g. WEATHER_ALERT, INCIDENT).
    Requires JWT authentication.
    """

    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Event.objects.filter(
            event_type__in=["WEATHER_ALERT", "INCIDENT"]
        )
        return queryset.order_by("-timestamp")


class UserNotificationListView(generics.ListAPIView):
    """
    List notifications for the authenticated user.
    Requires JWT authentication.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-timestamp")


# -------------------------------------------------
# LIVE VESSELS API (AIS Data)
# -------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def live_vessels_api(request):
    """
    Returns live vessel position data from AIS sources.
    Includes comprehensive error handling and fallback data.
    
    Query Parameters:
    - limit: Maximum number of vessels to return (default: 50)
    - imo: Filter by specific IMO number
    
    Requires JWT authentication.
    """
    try:
        # Ensure we have fallback vessel data
        FallbackDataService.ensure_minimum_vessel_data()
        
        # Initialize AIS service (API key would come from settings in production)
        ais_service = AISDataService()
        
        # Get query parameters with validation
        try:
            limit = int(request.query_params.get('limit', 50))
            if limit <= 0 or limit > 1000:
                limit = 50
        except (ValueError, TypeError):
            limit = 50
            
        imo_filter = request.query_params.get('imo', '').strip()
        
        # Fetch vessel data with error handling
        vessel_data = []
        api_success = True
        
        try:
            if imo_filter:
                vessel_data = ais_service.get_vessel_by_imo(imo_filter)
                vessel_data = [vessel_data] if vessel_data else []
            else:
                vessel_data = ais_service.get_live_vessel_positions(limit=limit)
                
        except Exception as ais_error:
            logger.warning(f"AIS service failed: {str(ais_error)}")
            api_success = False
            
            # Use fallback data from database or static data
            if imo_filter:
                try:
                    vessel = Vessel.objects.get(imo_number=imo_filter)
                    vessel_data = [{
                        'imo': vessel.imo_number,
                        'name': vessel.name,
                        'vessel_type': vessel.vessel_type,
                        'latitude': vessel.last_position_lat,
                        'longitude': vessel.last_position_lon,
                        'speed': 0.0,  # Unknown when using fallback
                        'heading': 0,   # Unknown when using fallback
                        'timestamp': vessel.last_update.isoformat() if vessel.last_update else None
                    }]
                except Vessel.DoesNotExist:
                    vessel_data = []
            else:
                # Use static fallback data
                vessel_data = FallbackDataService.get_fallback_vessel_data()[:limit]
        
        # Serialize the data
        try:
            serializer = LiveVesselSerializer(vessel_data, many=True)
            response_data = {
                'count': len(vessel_data),
                'vessels': serializer.data
            }
            
            # Add metadata about data source
            if not api_success:
                response_data['data_source'] = 'fallback'
                response_data['message'] = 'Using fallback data due to AIS service unavailability'
            else:
                response_data['data_source'] = 'live'
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as serializer_error:
            logger.error(f"Serialization error: {str(serializer_error)}", exc_info=True)
            
            # Return minimal fallback response
            return Response({
                'count': 0,
                'vessels': [],
                'data_source': 'fallback',
                'error': 'Data serialization failed'
            }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.warning(f"Invalid request parameters: {str(e)}")
        return Response(
            {'error': 'Invalid limit parameter. Must be a number between 1 and 1000.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Critical error in live_vessels_api: {str(e)}", exc_info=True)
        
        # Always return some data, even if it's just fallback
        fallback_data = FallbackDataService.get_fallback_vessel_data()
        return Response({
            'count': len(fallback_data),
            'vessels': fallback_data,
            'data_source': 'emergency_fallback',
            'error': 'Service temporarily unavailable'
        }, status=status.HTTP_200_OK)


# -------------------------------------------------
# EVENT CHECKS API
# -------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_event_checks_api(request):
    """
    Manually trigger event checks for high congestion, storms, and piracy risks.
    Creates events and notifications as needed.
    
    Requires JWT authentication and ADMIN role.
    """
    if request.user.role != 'ADMIN':
        return Response(
            {'error': 'Admin role required to trigger event checks'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        summary = run_all_event_checks()
        return Response({
            'message': 'Event checks completed successfully',
            'summary': summary
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to run event checks: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Failed to run event checks: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# -------------------------------------------------
# PORT ANALYTICS API
# -------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def port_congestion_analytics_api(request):
    """
    Get comprehensive port congestion analytics with UNCTAD-style statistics.
    
    Query Parameters:
    - refresh: Set to 'true' to force refresh from UNCTAD API
    
    Requires JWT authentication.
    """
    try:
        from core.services.port_analytics import PortAnalyticsService
        
        service = PortAnalyticsService()
        
        # Check if refresh is requested
        refresh_requested = request.query_params.get('refresh', '').lower() == 'true'
        
        if refresh_requested and request.user.role in ['ADMIN', 'ANALYST']:
            # Only admins and analysts can trigger refresh
            logger.info(f"Port analytics refresh requested by {request.user.username}")
            refresh_summary = service.refresh_all_port_analytics()
            
            return Response({
                'message': 'Port analytics refreshed successfully',
                'refresh_summary': refresh_summary,
                'dashboard_data': service.get_port_dashboard_data()
            }, status=status.HTTP_200_OK)
        
        # Return current dashboard data
        dashboard_data = service.get_port_dashboard_data()
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in port_congestion_analytics_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve port analytics data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ports_dashboard_api(request):
    """
    Get port dashboard data with comprehensive analytics.
    
    Requires JWT authentication.
    """
    try:
        from core.services.port_analytics import PortAnalyticsService
        
        service = PortAnalyticsService()
        dashboard_data = service.get_port_dashboard_data()
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in ports_dashboard_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve dashboard data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_port_analytics_api(request):
    """
    Manually refresh port analytics using UNCTAD data.
    
    Requires JWT authentication and ADMIN/ANALYST role.
    """
    if request.user.role not in ['ADMIN', 'ANALYST']:
        return Response(
            {'error': 'Admin or Analyst role required to refresh port analytics'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from core.services.port_analytics import PortAnalyticsService
        
        service = PortAnalyticsService()
        summary = service.refresh_all_port_analytics()
        
        return Response({
            'message': 'Port analytics refresh completed',
            'summary': summary
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to refresh port analytics: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Failed to refresh port analytics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# -------------------------------------------------
# VOYAGE HISTORY AND REPLAY API
# -------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vessel_history_api(request, vessel_id):
    """
    Get historical positions for a specific vessel.
    
    Query Parameters:
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    - limit: Maximum positions to return (default: 1000)
    
    Requires JWT authentication.
    """
    try:
        vessel = Vessel.objects.get(id=vessel_id)
    except Vessel.DoesNotExist:
        return Response(
            {'error': 'Vessel not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        from core.services.voyage_history import VoyageHistoryService
        from datetime import datetime
        
        # Parse query parameters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        limit = int(request.query_params.get('limit', 1000))
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get history data
        service = VoyageHistoryService()
        history_data = service.get_vessel_history(vessel, start_date, end_date, limit)
        
        return Response(history_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in vessel_history_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve vessel history'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def voyage_route_api(request, voyage_id):
    """
    Get the complete route for a specific voyage.
    
    Query Parameters:
    - include_interpolated: Include interpolated positions (default: false)
    
    Requires JWT authentication.
    """
    try:
        voyage = Voyage.objects.get(id=voyage_id)
    except Voyage.DoesNotExist:
        return Response(
            {'error': 'Voyage not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        from core.services.voyage_history import VoyageHistoryService
        
        include_interpolated = request.query_params.get('include_interpolated', 'false').lower() == 'true'
        
        service = VoyageHistoryService()
        route_data = service.get_voyage_route(voyage, include_interpolated)
        
        response_data = {
            'voyage': {
                'id': voyage.id,
                'vessel_name': voyage.vessel.name,
                'vessel_imo': voyage.vessel.imo_number,
                'port_from': voyage.port_from.name,
                'port_to': voyage.port_to.name,
                'departure_time': voyage.departure_time.isoformat(),
                'arrival_time': voyage.arrival_time.isoformat() if voyage.arrival_time else None,
                'status': voyage.status
            },
            'route': route_data,
            'total_positions': len(route_data),
            'include_interpolated': include_interpolated
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in voyage_route_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve voyage route'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def voyage_replay_api(request, voyage_id):
    """
    Generate replay data for a voyage.
    
    POST data:
    {
        "speed_multiplier": 1.0,
        "interpolate_gaps": true
    }
    
    Requires JWT authentication.
    """
    try:
        voyage = Voyage.objects.get(id=voyage_id)
    except Voyage.DoesNotExist:
        return Response(
            {'error': 'Voyage not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        from core.services.voyage_history import VoyageHistoryService
        
        # Parse request data
        speed_multiplier = float(request.data.get('speed_multiplier', 1.0))
        interpolate_gaps = request.data.get('interpolate_gaps', True)
        
        # Validate speed multiplier
        if speed_multiplier <= 0 or speed_multiplier > 100:
            return Response(
                {'error': 'Speed multiplier must be between 0.1 and 100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = VoyageHistoryService()
        replay_data = service.generate_replay_data(
            voyage=voyage,
            speed_multiplier=speed_multiplier,
            interpolate_gaps=interpolate_gaps,
            user=request.user
        )
        
        return Response(replay_data, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': f'Invalid parameter: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error in voyage_replay_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to generate replay data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def voyage_statistics_api(request, voyage_id):
    """
    Get comprehensive statistics for a voyage.
    
    Requires JWT authentication.
    """
    try:
        voyage = Voyage.objects.get(id=voyage_id)
    except Voyage.DoesNotExist:
        return Response(
            {'error': 'Voyage not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        from core.services.voyage_history import VoyageHistoryService
        
        service = VoyageHistoryService()
        statistics = service.get_voyage_statistics(voyage)
        
        return Response(statistics, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in voyage_statistics_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve voyage statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_vessel_position_api(request):
    """
    Manually record a vessel position.
    
    POST data:
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
    
    Requires JWT authentication and OPERATOR+ role.
    """
    if request.user.role not in ['ADMIN', 'OPERATOR', 'ANALYST']:
        return Response(
            {'error': 'Insufficient permissions to record positions'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from core.services.voyage_history import VoyageHistoryService
        from datetime import datetime
        
        # Validate required fields
        required_fields = ['vessel_id', 'latitude', 'longitude', 'timestamp']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'Missing required field: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get vessel
        try:
            vessel = Vessel.objects.get(id=request.data['vessel_id'])
        except Vessel.DoesNotExist:
            return Response(
                {'error': 'Vessel not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Parse and validate data
        try:
            latitude = float(request.data['latitude'])
            longitude = float(request.data['longitude'])
            timestamp = datetime.fromisoformat(request.data['timestamp'].replace('Z', '+00:00'))
            
            # Validate coordinates
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude must be between -180 and 180")
            
        except (ValueError, TypeError) as e:
            return Response(
                {'error': f'Invalid data format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Optional fields
        speed = request.data.get('speed')
        heading = request.data.get('heading')
        source = request.data.get('source', 'MANUAL')
        accuracy = request.data.get('accuracy')
        
        if speed is not None:
            speed = float(speed)
        if heading is not None:
            heading = int(heading)
            if not (0 <= heading <= 359):
                return Response(
                    {'error': 'Heading must be between 0 and 359'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if accuracy is not None:
            accuracy = float(accuracy)
        
        # Record position
        service = VoyageHistoryService()
        position = service.record_position(
            vessel=vessel,
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            speed=speed,
            heading=heading,
            source=source,
            accuracy=accuracy,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'message': 'Position recorded successfully',
            'position': {
                'id': position.id,
                'vessel_name': vessel.name,
                'latitude': position.latitude,
                'longitude': position.longitude,
                'timestamp': position.timestamp.isoformat(),
                'speed': position.speed,
                'heading': position.heading,
                'source': position.source,
                'voyage_id': position.voyage.id if position.voyage else None
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error in record_vessel_position_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to record position'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def voyage_audit_logs_api(request, voyage_id):
    """
    Get audit logs for a specific voyage.
    
    Query Parameters:
    - limit: Maximum logs to return (default: 100)
    - action: Filter by action type
    
    Requires JWT authentication and ADMIN/ANALYST role.
    """
    if request.user.role not in ['ADMIN', 'ANALYST']:
        return Response(
            {'error': 'Admin or Analyst role required to access audit logs'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        voyage = Voyage.objects.get(id=voyage_id)
    except Voyage.DoesNotExist:
        return Response(
            {'error': 'Voyage not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        from core.models import VoyageAuditLog
        
        # Parse query parameters
        limit = int(request.query_params.get('limit', 100))
        action_filter = request.query_params.get('action')
        
        # Build query
        logs_query = VoyageAuditLog.objects.filter(voyage=voyage)
        
        if action_filter:
            logs_query = logs_query.filter(action=action_filter)
        
        logs = logs_query.order_by('-timestamp')[:limit]
        
        # Format response
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'action': log.action,
                'description': log.description,
                'user': log.user.username if log.user else 'System',
                'timestamp': log.timestamp.isoformat(),
                'ip_address': log.ip_address,
                'metadata': log.metadata,
                'compliance_category': log.compliance_category
            })
        
        return Response({
            'voyage_id': voyage.id,
            'vessel_name': voyage.vessel.name,
            'logs': logs_data,
            'total_returned': len(logs_data),
            'filters': {
                'action': action_filter,
                'limit': limit
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in voyage_audit_logs_api: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve audit logs'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# -------------------------------------------------
# BACKGROUND JOBS API
# -------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_background_jobs_api(request):
    """
    Manually trigger background jobs for data updates.
    
    Query Parameters:
    - job: Specify which job to run ('all', 'ports', 'safety', 'vessels')
    
    Requires JWT authentication and ADMIN role.
    """
    if request.user.role != 'ADMIN':
        return Response(
            {'error': 'Admin role required to run background jobs'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    job_type = request.query_params.get('job', 'all')
    
    if job_type not in ['all', 'ports', 'safety', 'vessels']:
        return Response(
            {'error': 'Invalid job type. Must be one of: all, ports, safety, vessels'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        if job_type == 'all':
            summary = BackgroundJobService.run_all_background_jobs()
        elif job_type == 'ports':
            summary = BackgroundJobService.update_port_congestion()
        elif job_type == 'safety':
            summary = BackgroundJobService.update_safety_events()
        elif job_type == 'vessels':
            summary = BackgroundJobService.update_vessel_positions()
        
        return Response({
            'message': f'{job_type.title()} background job(s) completed',
            'summary': summary
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to run background job {job_type}: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Failed to run background job: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health_api(request):
    """
    Check system health and data availability.
    Returns status of various components and data sources.
    
    Requires JWT authentication.
    """
    try:
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check database connectivity
        try:
            port_count = Port.objects.count()
            vessel_count = Vessel.objects.count()
            event_count = Event.objects.count()
            notification_count = Notification.objects.count()
            
            health_status['components']['database'] = {
                'status': 'healthy',
                'ports': port_count,
                'vessels': vessel_count,
                'events': event_count,
                'notifications': notification_count
            }
        except Exception as db_error:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(db_error)
            }
            health_status['overall_status'] = 'degraded'
        
        # Check AIS service
        try:
            from core.services.ais_data import AISDataService
            ais_service = AISDataService()
            # Try to get a small sample
            test_data = ais_service.get_live_vessel_positions(limit=1)
            
            health_status['components']['ais_service'] = {
                'status': 'healthy',
                'sample_data_available': len(test_data) > 0
            }
        except Exception as ais_error:
            health_status['components']['ais_service'] = {
                'status': 'degraded',
                'error': str(ais_error),
                'fallback_available': True
            }
        
        # Check recent data updates
        try:
            from django.utils import timezone
            recent_threshold = timezone.now() - timezone.timedelta(hours=24)
            
            recent_events = Event.objects.filter(timestamp__gte=recent_threshold).count()
            recent_notifications = Notification.objects.filter(timestamp__gte=recent_threshold).count()
            
            health_status['components']['recent_activity'] = {
                'status': 'healthy',
                'events_24h': recent_events,
                'notifications_24h': recent_notifications
            }
        except Exception as activity_error:
            health_status['components']['recent_activity'] = {
                'status': 'unknown',
                'error': str(activity_error)
            }
        
        return Response(health_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}", exc_info=True)
        return Response({
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

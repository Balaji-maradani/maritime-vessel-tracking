from django.http import HttpResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Vessel, Port, Voyage, User, Event, Notification
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    VesselSerializer,
    NotificationCreateSerializer,
    PortCongestionSerializer,
    EventSerializer,
    NotificationSerializer,
    LiveVesselSerializer,
)
from .permissions import IsAnalyst, IsOperator
from .services.ais_data import AISDataService


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
    Requires JWT authentication.
    """

    serializer_class = PortCongestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Port.objects.all().order_by("-congestion_score")

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
# SUBSCRIBE TO VESSEL ALERTS
# -------------------------------------------------
class SubscribeVesselAlertView(generics.CreateAPIView):
    """
    Creates a notification subscription/entry for the authenticated user.
    Event is optional; used for generic vessel alerts.
    """

    serializer_class = NotificationCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


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
    Currently uses mock data but structured for real API integration.
    
    Query Parameters:
    - limit: Maximum number of vessels to return (default: 50)
    - imo: Filter by specific IMO number
    
    Requires JWT authentication.
    """
    try:
        # Initialize AIS service (API key would come from settings in production)
        ais_service = AISDataService()
        
        # Get query parameters
        limit = int(request.query_params.get('limit', 50))
        imo_filter = request.query_params.get('imo')
        
        # Fetch vessel data
        if imo_filter:
            vessel_data = ais_service.get_vessel_by_imo(imo_filter)
            vessel_data = [vessel_data] if vessel_data else []
        else:
            vessel_data = ais_service.get_live_vessel_positions(limit=limit)
        
        # Serialize the data
        serializer = LiveVesselSerializer(vessel_data, many=True)
        
        return Response({
            'count': len(vessel_data),
            'vessels': serializer.data
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': 'Invalid limit parameter. Must be a number.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch vessel data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

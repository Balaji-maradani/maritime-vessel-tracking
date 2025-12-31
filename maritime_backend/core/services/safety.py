"""
Safety and weather risk integration using NOAA data.

Responsibilities:
- Fetch weather/safety data from NOAA-style API
- Detect storms and high‑risk zones
- Create corresponding safety Events and Notifications
"""

import logging
from typing import Dict, Any, Iterable, List, Optional, Tuple

import requests
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from core.models import Vessel, Event, Notification, User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _get_noaa_config() -> Tuple[str, Optional[str]]:
    """
    Read NOAA API configuration from Django settings.

    Expected settings (optional but recommended):
    - NOAA_WEATHER_URL: Base URL for NOAA weather/safety endpoint
    - NOAA_API_KEY: API token or key (if required)
    """
    base_url = getattr(
        settings,
        "NOAA_WEATHER_URL",
        "https://example-noaa.gov/api/weather",  # placeholder
    )
    api_key = getattr(settings, "NOAA_API_KEY", None)
    if not api_key:
        logger.warning("NOAA_API_KEY is not configured; using anonymous access if allowed.")
    return base_url, api_key


# ---------------------------------------------------------------------------
# Fetching NOAA data
# ---------------------------------------------------------------------------

def fetch_noaa_weather(params: Dict[str, Any] | None = None) -> Iterable[Dict[str, Any]]:
    """
    Fetch raw weather/safety data from NOAA.

    This is intentionally generic; you can adapt param names and the
    endpoint format to your exact NOAA integration.
    """
    base_url, api_key = _get_noaa_config()
    query_params = params.copy() if params else {}

    # Common NOAA patterns: API key as query param or header.
    if api_key:
        query_params.setdefault("api_key", api_key)

    try:
        response = requests.get(base_url, params=query_params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch NOAA weather data: %s", exc, exc_info=True)
        return []

    try:
        data = response.json()
    except ValueError:
        logger.error("NOAA response is not valid JSON")
        return []

    # Accept either a list or dict with 'features' / 'results'.
    if isinstance(data, dict):
        if "features" in data:
            # Many NOAA APIs are GeoJSON-like with 'features'.
            return data["features"] or []
        if "results" in data:
            return data["results"] or []

    if isinstance(data, list):
        return data

    logger.warning("Unexpected NOAA response format: %s", type(data))
    return []


# ---------------------------------------------------------------------------
# Risk detection
# ---------------------------------------------------------------------------

def _extract_weather_point(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a NOAA record into a simpler structure:
    {
        'lat': float | None,
        'lon': float | None,
        'wind_speed': float | None,
        'wave_height': float | None,
        'storm': bool,
        'description': str,
    }
    """
    # Support GeoJSON feature style: { "geometry": {"coordinates": [lon, lat]}, "properties": {...}}
    geometry = record.get("geometry") or {}
    properties = record.get("properties") or record

    coords = geometry.get("coordinates") or []
    lon = coords[0] if len(coords) >= 1 else properties.get("lon") or properties.get("longitude")
    lat = coords[1] if len(coords) >= 2 else properties.get("lat") or properties.get("latitude")

    wind_speed = properties.get("windSpeed") or properties.get("wind_speed")
    wave_height = properties.get("waveHeight") or properties.get("wave_height")
    hazard = (properties.get("hazard") or properties.get("phenomenon") or "").upper()
    description = (
        properties.get("description")
        or properties.get("summary")
        or properties.get("headline")
        or "Weather alert"
    )

    # Simple storm/high‑risk detection heuristics.
    is_storm = "STORM" in hazard or "CYCLONE" in hazard or "HURRICANE" in hazard

    try:
        wind_speed_val = float(wind_speed) if wind_speed is not None else None
    except (TypeError, ValueError):
        wind_speed_val = None

    try:
        wave_height_val = float(wave_height) if wave_height is not None else None
    except (TypeError, ValueError):
        wave_height_val = None

    # Threshold-based risk detection if no explicit storm code.
    if not is_storm:
        if (wind_speed_val is not None and wind_speed_val >= 25) or (
            wave_height_val is not None and wave_height_val >= 4
        ):
            is_storm = True

    return {
        "lat": float(lat) if lat is not None else None,
        "lon": float(lon) if lon is not None else None,
        "wind_speed": wind_speed_val,
        "wave_height": wave_height_val,
        "storm": is_storm,
        "description": description,
    }


def detect_high_risk_zones(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    From a collection of NOAA records, return only those representing
    storms or high‑risk conditions.
    """
    high_risk: List[Dict[str, Any]] = []

    for raw in records:
        point = _extract_weather_point(raw)
        if point["storm"]:
            high_risk.append(point)

    return high_risk


def _find_nearby_vessels(lat: float, lon: float, max_delta: float = 2.0) -> Iterable[Vessel]:
    """
    Very simple bounding‑box based proximity search for vessels.
    This is not geospatially exact but good enough for a first pass.
    """
    if lat is None or lon is None:
        return Vessel.objects.none()

    return Vessel.objects.filter(
        last_position_lat__isnull=False,
        last_position_lon__isnull=False,
        last_position_lat__gte=lat - max_delta,
        last_position_lat__lte=lat + max_delta,
        last_position_lon__gte=lon - max_delta,
        last_position_lon__lte=lon + max_delta,
    )


# ---------------------------------------------------------------------------
# Event + Notification creation
# ---------------------------------------------------------------------------

def _create_weather_event_for_vessel(vessel: Vessel, description: str, lat: float, lon: float) -> Event:
    """
    Create a WEATHER_ALERT event tied to a specific vessel.
    """
    location_str = f"Lat {lat:.3f}, Lon {lon:.3f}" if lat is not None and lon is not None else "Unknown"
    event = Event.objects.create(
        vessel=vessel,
        event_type="WEATHER_ALERT",
        location=location_str,
        details=description,
    )
    return event


def _notify_users_for_event(event: Event) -> None:
    """
    Create notifications for relevant users when a safety event is triggered.

    Current strategy:
    - Notify all ADMIN and OPERATOR users.
    You can refine this to role-based or subscription-based rules.
    """
    users = User.objects.filter(role__in=["ADMIN", "OPERATOR"])
    if not users.exists():
        return

    message = f"Safety alert for {event.vessel.name}: {event.details}"
    notifications = [
        Notification(
            user=u,
            vessel=event.vessel,
            event=event,
            message=message,
            notification_type="EVENT_ALERT",
        )
        for u in users
    ]
    Notification.objects.bulk_create(notifications)


def trigger_safety_events_from_noaa(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    High-level service:
    - Fetch NOAA weather/safety data
    - Detect storms / high‑risk zones
    - For each risk zone, link to nearby vessels
    - Create WEATHER_ALERT events and corresponding notifications

    Returns a summary dict with counts.
    """
    raw_records = list(fetch_noaa_weather(params=params))
    high_risk_points = detect_high_risk_zones(raw_records)

    events_created = 0
    notifications_created = 0
    zones_without_vessels = 0

    for point in high_risk_points:
        lat = point["lat"]
        lon = point["lon"]
        description = point["description"]

        nearby_vessels = list(_find_nearby_vessels(lat, lon))
        if not nearby_vessels:
            zones_without_vessels += 1
            continue

        for vessel in nearby_vessels:
            event = _create_weather_event_for_vessel(vessel, description, lat, lon)
            events_created += 1

            # Notify users and count how many notifications were created.
            before_count = Notification.objects.count()
            _notify_users_for_event(event)
            after_count = Notification.objects.count()
            notifications_created += max(after_count - before_count, 0)

    summary = {
        "fetched": len(raw_records),
        "high_risk_zones": len(high_risk_points),
        "events_created": events_created,
        "notifications_created": notifications_created,
        "zones_without_vessels": zones_without_vessels,
    }

    logger.info("NOAA safety integration summary: %s", summary)
    return summary



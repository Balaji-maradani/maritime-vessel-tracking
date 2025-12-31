import logging
from typing import Iterable, Tuple, Dict, Any

import requests
from django.conf import settings
from django.utils import timezone

from core.models import Vessel

logger = logging.getLogger(__name__)


def _get_aishub_config() -> Tuple[str, str]:
    """
    Get AIS Hub API configuration from Django settings.

    Expected settings:
    - AISHUB_API_URL: Base URL for AIS Hub endpoint
    - AISHUB_API_KEY: API key/token for authentication
    """
    api_url = getattr(
        settings,
        "AISHUB_API_URL",
        "https://example-ais-hub.com/api/vessels",  # placeholder
    )
    api_key = getattr(settings, "AISHUB_API_KEY", None)

    if not api_key:
        logger.warning("AISHUB_API_KEY is not configured in settings.")

    return api_url, api_key


def fetch_live_vessel_data(params: Dict[str, Any] | None = None) -> Iterable[Dict[str, Any]]:
    """
    Call AIS Hub API and return raw vessel data.

    This function only handles the HTTP call + basic error handling.
    Data mapping into Django models is handled separately.
    """
    api_url, api_key = _get_aishub_config()

    headers = {}
    query_params = params.copy() if params else {}

    # Common patterns: API key in header or query string.
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        # If AIS Hub expects key as query param instead, you can also do:
        # query_params.setdefault("api_key", api_key)

    try:
        response = requests.get(api_url, headers=headers, params=query_params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch AIS data from %s: %s", api_url, exc, exc_info=True)
        return []

    try:
        data = response.json()
    except ValueError:
        logger.error("AIS Hub response is not valid JSON")
        return []

    # Assume data is either a list of vessels or an object with 'vessels' key.
    if isinstance(data, dict) and "vessels" in data:
        return data["vessels"] or []
    if isinstance(data, list):
        return data

    logger.warning("Unexpected AIS Hub response format: %s", type(data))
    return []


def _map_ais_record_to_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a single AIS Hub record into Vessel model fields.

    Adjust the keys here to match the actual AIS Hub API response.
    """
    # Example key names; replace with real AIS Hub field names.
    imo = record.get("imo") or record.get("imo_number")
    name = record.get("name") or record.get("vessel_name")
    vessel_type = record.get("type") or record.get("ship_type") or ""
    flag = record.get("flag") or record.get("country") or ""
    cargo_type = record.get("cargo") or record.get("cargo_type") or ""
    operator = record.get("operator") or ""

    lat = record.get("lat") or record.get("latitude")
    lon = record.get("lon") or record.get("longitude")

    return {
        "imo_number": str(imo) if imo is not None else "",
        "name": name or "Unknown Vessel",
        "vessel_type": vessel_type or "Unknown",
        "flag": flag or "Unknown",
        "cargo_type": cargo_type or "Unknown",
        "operator": operator or "Unknown",
        "last_position_lat": lat,
        "last_position_lon": lon,
        # last_update is auto-managed by the model (auto_now=True)
    }


def upsert_vessel_from_ais_record(record: Dict[str, Any]) -> Vessel | None:
    """
    Create or update a Vessel instance from a single AIS Hub record.

    Vessels are identified by their IMO number. If IMO is missing, the
    record is skipped and None is returned.
    """
    fields = _map_ais_record_to_fields(record)
    imo = fields.get("imo_number")

    if not imo:
        logger.warning("Skipping AIS record without IMO: %s", record)
        return None

    defaults = fields.copy()
    # These fields never change the primary identifier itself.
    defaults.pop("imo_number", None)

    vessel, created = Vessel.objects.update_or_create(
        imo_number=imo,
        defaults=defaults,
    )

    logger.info(
        "Vessel %s (%s) %s via AIS Hub",
        vessel.name,
        vessel.imo_number,
        "created" if created else "updated",
    )

    return vessel


def refresh_vessel_positions(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    High-level service:
    - Fetch live vessel data from AIS Hub
    - Upsert Vessel records in the database

    Returns a summary dict with counts.
    """
    records = list(fetch_live_vessel_data(params=params))
    processed = 0
    created = 0
    updated = 0

    for record in records:
        before = timezone.now()
        vessel = upsert_vessel_from_ais_record(record)
        if vessel is None:
            continue

        processed += 1
        # We can't directly know created/updated here without changing
        # `upsert_vessel_from_ais_record` to return that flag, so we only
        # track processed in this minimal implementation.
        # If needed, extend `upsert_vessel_from_ais_record` to return (vessel, created).

    summary = {
        "fetched": len(records),
        "processed": processed,
        "created": created,
        "updated": updated,
    }

    logger.info("AIS Hub sync summary: %s", summary)
    return summary



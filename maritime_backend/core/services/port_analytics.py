"""
Service utilities for integrating UNCTAD port statistics
and updating congestion-related metrics on the Port model.
"""

import logging
from typing import Dict, Any, Iterable

import requests
from django.conf import settings

from core.models import Port

logger = logging.getLogger(__name__)


def _get_unctad_config() -> str:
    """
    Read UNCTAD API base URL from settings.

    Expected setting:
    - UNCTAD_PORT_STATS_URL: Base URL for UNCTAD port statistics endpoint
    """
    return getattr(
        settings,
        "UNCTAD_PORT_STATS_URL",
        "https://example-unctad.org/api/port-stats",  # placeholder
    )


def fetch_unctad_port_stats(params: Dict[str, Any] | None = None) -> Iterable[Dict[str, Any]]:
    """
    Fetch raw port statistics from the UNCTAD API.

    This function is deliberately generic; adjust param names and
    auth headers to match your actual UNCTAD integration.
    """
    base_url = _get_unctad_config()
    query_params = params.copy() if params else {}

    try:
        response = requests.get(base_url, params=query_params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch UNCTAD port statistics: %s", exc, exc_info=True)
        return []

    try:
        data = response.json()
    except ValueError:
        logger.error("UNCTAD response is not valid JSON")
        return []

    # Support either list or dict with 'results' key, etc.
    if isinstance(data, dict):
        if "results" in data:
            return data["results"] or []
        if "ports" in data:
            return data["ports"] or []

    if isinstance(data, list):
        return data

    logger.warning("Unexpected UNCTAD response format: %s", type(data))
    return []


def _map_unctad_record_to_metrics(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a single UNCTAD record to congestion score and wait time.

    Adjust the key names to match the real UNCTAD payload structure.
    """
    # Example keys; replace/adapt to your real data.
    congestion = record.get("congestion_score") or record.get("congestionIndex")
    avg_wait_hours = record.get("avg_wait_time_hours") or record.get("averageWaitingTime")

    metrics: Dict[str, Any] = {}
    if congestion is not None:
        # Normalize congestion to 0–10 if needed.
        try:
            metrics["congestion_score"] = float(congestion)
        except (TypeError, ValueError):
            logger.debug("Invalid congestion_score in record: %s", record)

    if avg_wait_hours is not None:
        try:
            metrics["avg_wait_time"] = float(avg_wait_hours)
        except (TypeError, ValueError):
            logger.debug("Invalid avg_wait_time in record: %s", record)

    return metrics


def update_port_from_unctad_record(record: Dict[str, Any]) -> Port | None:
    """
    Update a single Port instance from one UNCTAD statistics record.

    Ports are matched by name + country (can be refined if you have
    UN/LOCODE or another unique identifier in your model).
    """
    name = record.get("port_name") or record.get("name")
    country = record.get("country") or record.get("country_name")

    if not name or not country:
        logger.debug("Skipping UNCTAD record without name/country: %s", record)
        return None

    try:
        port = Port.objects.get(name=name, country=country)
    except Port.DoesNotExist:
        logger.debug("No matching Port found for UNCTAD record: %s, %s", name, country)
        return None

    metrics = _map_unctad_record_to_metrics(record)
    if not metrics:
        return port

    for field, value in metrics.items():
        setattr(port, field, value)

    port.save(update_fields=list(metrics.keys()) + ["last_update"])
    logger.info(
        "Updated Port %s (%s) congestion metrics from UNCTAD",
        port.name,
        port.country,
    )
    return port


def refresh_port_congestion(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    High-level service:
    - Fetch UNCTAD statistics
    - Update congestion_score and avg_wait_time on matching Port records

    Returns a summary dict with counts.
    """
    records = list(fetch_unctad_port_stats(params=params))
    updated = 0
    skipped = 0

    for record in records:
        port = update_port_from_unctad_record(record)
        if port is None:
            skipped += 1
        else:
            updated += 1

    summary = {
        "fetched": len(records),
        "updated": updated,
        "skipped": skipped,
    }

    logger.info("UNCTAD port congestion sync summary: %s", summary)
    return summary



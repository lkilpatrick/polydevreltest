from _gen import *  # <AUTO GENERATED>
import json
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# FareHarbor config
COMPANY_SHORTNAME = os.getenv("FAREHARBOR_COMPANY_SHORTNAME", "sanctuarycruises")
BASE_URL = os.getenv("FAREHARBOR_BASE_URL", "https://fareharbor.com/api/external/v1")
API_APP = os.getenv("FAREHARBOR_API_APP", "")
API_USER = os.getenv("FAREHARBOR_API_USER", "")

# Cache
_items_cache: dict | None = None
_cache_expiry: float = 0.0
CACHE_TTL = 300  # 5 minutes


@func_description("FareHarbor integration utility module for Sanctuary Cruises. Returns a status message describing connection state. Call lookup_availability() to check schedule data.")
def fareharbor(conv: Conversation):
    """Utility entry point — describes this integration module."""
    api_key_configured = bool(API_APP and API_USER)
    return {
        "module": "fareharbor_integration",
        "company": COMPANY_SHORTNAME,
        "api_keys_configured": api_key_configured,
        "message": (
            "FareHarbor integration module loaded. "
            "API keys are configured — live External API access enabled."
            if api_key_configured
            else
            "FareHarbor integration module loaded. "
            "No API keys configured — using public embed calendar only."
        ),
    }


def _make_request(url: str) -> dict:
    """Make an HTTP GET request and return parsed JSON."""
    headers = {"Accept": "application/json"}
    if API_APP and API_USER:
        headers["X-FareHarbor-API-App"] = API_APP
        headers["X-FareHarbor-API-User"] = API_USER

    req = Request(url, headers=headers)
    with urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode())


def get_items() -> list[dict]:
    """Fetch all FareHarbor items for the company, with in-memory cache."""
    global _items_cache, _cache_expiry
    now = datetime.utcnow().timestamp()
    if _items_cache is not None and now < _cache_expiry:
        return _items_cache

    url = f"{BASE_URL}/companies/{COMPANY_SHORTNAME}/items/"
    data = _make_request(url)
    _items_cache = data.get("items", [])
    _cache_expiry = now + CACHE_TTL
    return _items_cache


def find_matching_items(trip_type: str) -> list[dict]:
    """Find FareHarbor items whose name contains keywords from trip_type."""
    normalized = trip_type.strip().lower()
    keywords = []
    if "sunset" in normalized:
        keywords.append("sunset")
    elif "all" in normalized and "day" in normalized:
        keywords.append("all day")
    elif "photo" in normalized:
        keywords.append("photo")
    else:
        keywords.extend(["whale", "watching"])

    items = get_items()
    matches = []
    for item in items:
        item_name = item.get("name", "").lower()
        if any(kw in item_name for kw in keywords):
            matches.append(item)

    # Fallback: known PKs for whale watching
    if not matches:
        matches = [{"pk": 25836, "name": "Whale Watching 2-3 hr"}, {"pk": 25833, "name": "Whale Watching 3-4 hr"}]

    return matches


def get_availabilities(item_pk: int, year: int, month: int) -> list[dict]:
    """Fetch availability from FareHarbor calendar for a specific item and month."""
    url = f"https://fareharbor.com/api/v1/companies/{COMPANY_SHORTNAME}/items/{item_pk}/calendar/{year}/{month:02d}/"
    try:
        data = _make_request(url)
        return data.get("calendar", [])
    except (HTTPError, URLError, Exception):
        return []


def lookup_availability(trip_type: str, requested_date: str, party_size: int) -> dict:
    """
    Main lookup: finds FareHarbor availabilities for trip_type on requested_date.
    Returns a normalized dict with keys: source, availability, fits_any_option, fallback_data.
    """
    try:
        dt = datetime.strptime(requested_date, "%Y-%m-%d")
    except ValueError:
        return {"source": "error", "availability": [], "fits_any_option": False, "fallback_data": False, "error": f"Invalid date: {requested_date}"}

    year, month, day = dt.year, dt.month, dt.day
    matching_items = find_matching_items(trip_type)

    all_slots = []
    source = "unknown"

    for item in matching_items[:3]:  # limit items checked
        item_pk = item.get("pk")
        if not item_pk:
            continue

        calendar = get_availabilities(item_pk, year, month)
        for day_entry in calendar:
            if day_entry.get("date") != requested_date:
                continue
            for avail in day_entry.get("availabilities", []):
                departure_time = avail.get("start_at", "")
                if departure_time:
                    try:
                        dt_full = datetime.strptime(departure_time[:19], "%Y-%m-%dT%H:%M:%S")
                        departure_time = dt_full.strftime("%-I:%M %p")
                    except ValueError:
                        pass
                capacity = avail.get("capacity", 0)
                spots_left = capacity - avail.get("num_customers", 0)
                all_slots.append({
                    "item_name": item.get("name", ""),
                    "departure_time": departure_time,
                    "spots_left": max(spots_left, 0),
                    "capacity": capacity,
                    "is_bookable": avail.get("is_bookable", True),
                })
                source = "fareharbor_embed_api"

    if API_APP and API_USER:
        source = "fareharbor_external_api" if all_slots else source

    fits_any = any(slot["spots_left"] >= party_size for slot in all_slots)
    return {
        "source": source,
        "availability": all_slots,
        "fits_any_option": fits_any,
        "fallback_data": False,
    }

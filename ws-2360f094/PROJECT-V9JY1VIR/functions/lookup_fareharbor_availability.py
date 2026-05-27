from _gen import *  # <AUTO GENERATED>
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@func_description('Lookup live FareHarbor availability for Sanctuary Cruises')
@func_parameter('trip_type', 'Requested trip type, such as whale watching, sunset cruise, photography tour, or private charter')
@func_parameter('requested_date', 'Desired trip date from the caller, for example 2026-06-03')
@func_parameter('adults', 'Number of adults in the party')
@func_parameter('children', 'Number of children in the party')
def lookup_fareharbor_availability(conv: Conversation, trip_type: str, requested_date: str, adults: int, children: int):
  def format_time(timestamp: str) -> str:
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
      try:
        parsed = datetime.strptime(timestamp, fmt)
        return parsed.strftime("%I:%M %p").lstrip("0")
      except ValueError:
        continue
    return timestamp

  def duration_text(start_at: str, end_at: str) -> str:
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
      try:
        start_dt = datetime.strptime(start_at, fmt)
        end_dt = datetime.strptime(end_at, fmt)
        hours = max(1, round((end_dt - start_dt).total_seconds() / 3600))
        return f"About {hours} hour{'s' if hours != 1 else ''}"
      except ValueError:
        continue
    return "Unknown"

  def get_trip_keywords(resolved_trip_type: str):
    mapping = {
      "whale watching": ["whale", "watch"],
      "sunset cruise": ["sunset"],
      "photography tour": ["photo", "photography"],
    }
    return mapping.get(resolved_trip_type, [resolved_trip_type])

  def fetch_json(url: str, headers=None):
    if headers is None:
      headers = {}
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=15) as response:
      return json.loads(response.read().decode("utf-8"))

  def read_whale_watch_snapshot(date_value: str):
    try:
      requested = datetime.strptime(date_value, "%Y-%m-%d")
      snapshot_file = Path(__file__).resolve().parents[1] / "data" / "whale_watch_schedule_next_3_months.json"
      payload = json.loads(snapshot_file.read_text(encoding="utf-8"))
      month_key = requested.strftime("%Y-%m")
      date_label = f"{requested.strftime('%A, %B')} {requested.day}, {requested.year}"
      return payload.get("months", {}).get(month_key, {}).get(date_label, [])
    except (ValueError, OSError, json.JSONDecodeError):
      return []

  def resolve_item_pk_external(company_shortname: str, resolved_trip_type: str, headers: dict):
    env_key = f"FH_{resolved_trip_type.upper().replace(' ', '_')}_ITEM_PK"
    env_value = os.environ.get(env_key)
    if env_value and env_value.isdigit():
      return int(env_value)

    items_url = f"https://fareharbor.com/api/external/v1/companies/{company_shortname}/items/?detailed=no&require_future_availabilities=yes"
    items_payload = fetch_json(items_url, headers)
    keywords = get_trip_keywords(resolved_trip_type)
    for item in items_payload.get("items", []):
      search_text = f"{str(item.get('name', '')).lower()} {str(item.get('headline', '')).lower()}"
      if all(keyword in search_text for keyword in keywords):
        return item.get("pk")
    return None

  def live_external(company_shortname: str, resolved_trip_type: str, date_value: str, group_size: int, headers: dict):
    item_pk = resolve_item_pk_external(company_shortname, resolved_trip_type, headers)
    if not item_pk:
      return None

    url = (
      f"https://fareharbor.com/api/external/v1/companies/{company_shortname}"
      f"/items/{item_pk}/minimal/availabilities/date/{date_value}/?bookable_only=yes"
    )
    payload = fetch_json(url, headers)
    availabilities = payload.get("availabilities", [])
    options = []
    for availability in availabilities:
      start_at = availability.get("start_at")
      end_at = availability.get("end_at")
      if not start_at:
        continue
      options.append(
        {
          "departure_time": format_time(start_at),
          "duration": duration_text(start_at, end_at) if end_at else "Unknown",
          "status": availability.get("online_booking_status", "unknown"),
          "spots_left": availability.get("capacity"),
          "availability_pk": availability.get("pk"),
          "booking_url": f"https://fareharbor.com/embeds/book/{company_shortname}/",
        }
      )

    spots_known = bool(options) and all(option.get("spots_left") is not None for option in options)
    fits_any = any(group_size <= option["spots_left"] for option in options) if group_size > 0 and spots_known else bool(options)
    return {
      "trip_type": resolved_trip_type,
      "requested_date": date_value,
      "party_size": group_size,
      "availability": options,
      "fits_any_option": fits_any,
      "recommendation": "" if fits_any else "Group size appears larger than current online capacity. Offer another departure or crew handoff.",
      "mock_data": False,
      "source": "fareharbor_external_api",
      "note": "Live FareHarbor data. Final booking and payment occur in FareHarbor.",
    }

  def resolve_item_pk_embed(company_shortname: str, resolved_trip_type: str):
    env_key = f"FH_{resolved_trip_type.upper().replace(' ', '_')}_ITEM_PK"
    env_value = os.environ.get(env_key)
    if env_value and env_value.isdigit():
      return int(env_value)

    flow_id = os.environ.get("FH_EMBED_FLOW_ID", "1127725")
    flow_url = f"https://fareharbor.com/api/embed/{company_shortname}/flow-node/{flow_id}/v1/"
    payload = fetch_json(flow_url)
    keywords = get_trip_keywords(resolved_trip_type)
    first_item_id = None
    for child in payload.get("children", []):
      if child.get("type") != "item":
        continue
      item_id = child.get("id")
      if first_item_id is None and item_id:
        first_item_id = item_id
      search_text = f"{str(child.get('heading', '')).lower()} {str(child.get('subheading', '')).lower()}"
      if all(keyword in search_text for keyword in keywords):
        return item_id
    return first_item_id

  def live_embed(company_shortname: str, resolved_trip_type: str, date_value: str, group_size: int):
    item_pk = resolve_item_pk_embed(company_shortname, resolved_trip_type)
    if not item_pk:
      return None

    requested = datetime.strptime(date_value, "%Y-%m-%d")
    url = (
      f"https://fareharbor.com/api/v1/companies/{company_shortname}/items/{item_pk}"
      f"/calendar/{requested.year:04d}/{requested.month:02d}/"
      "?allow_grouped=yes&bookable_only=no&asn=&path=1&is_fh_app=no"
    )
    payload = fetch_json(url)
    day_entry = None
    for week in payload.get("calendar", {}).get("weeks", []):
      for day in week.get("days", []):
        if day.get("at") == date_value:
          day_entry = day
          break
      if day_entry:
        break
    if not day_entry:
      return None

    options = []
    for availability in day_entry.get("availabilities", []):
      start_at = str(availability.get("start_at", ""))
      end_at = str(availability.get("end_at", ""))
      if not start_at:
        continue
      is_bookable = bool(availability.get("is_bookable")) and not bool(availability.get("is_sold_out"))
      approx_capacity = availability.get("approximate_available_capacity")
      book_path = str(availability.get("book_url", "")).strip()
      options.append(
        {
          "departure_time": format_time(start_at),
          "duration": duration_text(start_at, end_at) if end_at else "Unknown",
          "status": "available" if is_bookable else "unavailable",
          "spots_left": approx_capacity if isinstance(approx_capacity, int) and approx_capacity > 0 else None,
          "availability_pk": availability.get("pk"),
          "booking_url": f"https://fareharbor.com{book_path}" if book_path.startswith("/") else f"https://fareharbor.com/embeds/book/{company_shortname}/",
        }
      )

    spots_known = bool(options) and all(option.get("spots_left") is not None for option in options)
    fits_any = any(group_size <= option["spots_left"] for option in options) if group_size > 0 and spots_known else bool(options)
    return {
      "trip_type": resolved_trip_type,
      "requested_date": date_value,
      "party_size": group_size,
      "availability": options,
      "fits_any_option": fits_any,
      "recommendation": "" if fits_any else "Group size appears larger than current online capacity. Offer another departure or crew handoff.",
      "mock_data": False,
      "source": "fareharbor_embed_api",
      "note": "Live FareHarbor data. Final booking and payment occur in FareHarbor.",
    }

  normalized = (trip_type or "").strip().lower()
  party_size = max(0, int(adults or 0)) + max(0, int(children or 0))

  aliases = {
    "whale watching": "whale watching",
    "whale": "whale watching",
    "standard whale watching": "whale watching",
    "sunset": "sunset cruise",
    "sunset cruise": "sunset cruise",
    "sunset whale watching": "sunset cruise",
    "photography": "photography tour",
    "photography tour": "photography tour",
    "marine wildlife photography tour": "photography tour",
    "private": "private charter",
    "private charter": "private charter",
    "charter": "private charter",
  }

  trip_key = aliases.get(normalized, normalized)
  if trip_key not in ("whale watching", "sunset cruise", "photography tour", "private charter"):
    trip_key = "whale watching"

  if trip_key == "private charter":
    return {
      "trip_type": trip_key,
      "requested_date": requested_date,
      "party_size": party_size,
      "human_required": True,
      "status": "human_required",
      "booking_url": "https://fareharbor.com/embeds/book/sanctuarycruises/",
      "message": "Private charters require crew follow-up for logistics and pricing.",
      "mock_data": False,
      "source": "human_handoff_required",
    }

  company_shortname = os.environ.get("FH_COMPANY_SHORTNAME", "sanctuarycruises")
  app_key = os.environ.get("FH_API_APP", "")
  user_key = os.environ.get("FH_API_USER", "")

  if app_key and user_key:
    headers = {
      "Accept": "application/json",
      "X-FareHarbor-API-App": app_key,
      "X-FareHarbor-API-User": user_key,
    }
    try:
      response = live_external(company_shortname, trip_key, requested_date, party_size, headers)
      if response and response.get("availability") is not None:
        return response
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
      pass

  try:
    response = live_embed(company_shortname, trip_key, requested_date, party_size)
    if response and response.get("availability") is not None:
      return response
  except (HTTPError, URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
    pass

  if trip_key == "whale watching":
    snapshot_times = read_whale_watch_snapshot(requested_date)
    if snapshot_times:
      options = []
      for time in snapshot_times:
        options.append(
          {
            "departure_time": time,
            "duration": "Up to 4 hours" if time in ("11:30 AM", "12:00 PM", "12:30 PM") else "Up to 3-4 hours",
            "status": "availability_snapshot",
            "spots_left": None,
            "booking_url": f"https://fareharbor.com/embeds/book/{company_shortname}/",
          }
        )

      return {
        "trip_type": trip_key,
        "requested_date": requested_date,
        "party_size": party_size,
        "availability": options,
        "fits_any_option": True,
        "recommendation": "These departure times come from a recent FareHarbor calendar snapshot. Confirm live seat counts before booking.",
        "mock_data": False,
        "fallback_data": True,
        "source": "fareharbor_calendar_snapshot",
        "note": "Fallback to local snapshot because live lookup was unavailable.",
      }

  return {
    "trip_type": trip_key,
    "requested_date": requested_date,
    "party_size": party_size,
    "availability": [],
    "fits_any_option": False,
    "human_required": True,
    "status": "unavailable",
    "recommendation": "Live FareHarbor availability could not be retrieved right now. Offer to connect the caller with crew.",
    "mock_data": False,
    "source": "live_lookup_failed",
  }

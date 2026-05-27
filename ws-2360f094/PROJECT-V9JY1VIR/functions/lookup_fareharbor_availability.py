from _gen import *  # <AUTO GENERATED>
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@func_description("Lookup mock FareHarbor availability for Sanctuary Cruises demo calls")
@func_parameter("trip_type", "Requested trip type, such as whale watching, sunset cruise, photography tour, or private charter")
@func_parameter("requested_date", "Desired trip date from the caller, for example 2026-06-03")
@func_parameter("adults", "Number of adults in the party")
@func_parameter("children", "Number of children in the party")
def lookup_fareharbor_availability(
  conv: Conversation,
  trip_type: str,
  requested_date: str,
  adults: int,
  children: int,
):
  def format_time(timestamp: str) -> str:
    try:
      parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
      # Some embed endpoints return local timestamps without timezone offsets.
      parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    return parsed.strftime("%I:%M %p").lstrip("0")

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
      payload = response.read().decode("utf-8")
      return json.loads(payload)

  def resolve_item_pk(company_shortname: str, resolved_trip_type: str, headers: dict):
    env_key = f"FH_{resolved_trip_type.upper().replace(' ', '_')}_ITEM_PK"
    env_value = os.environ.get(env_key)
    if env_value and env_value.isdigit():
      return int(env_value)

    items_url = f"https://fareharbor.com/api/external/v1/companies/{company_shortname}/items/?detailed=no&require_future_availabilities=yes"
    items_payload = fetch_json(items_url, headers)
    items = items_payload.get("items", [])
    keywords = get_trip_keywords(resolved_trip_type)

    for item in items:
      name = str(item.get("name", "")).lower()
      headline = str(item.get("headline", "")).lower()
      search_text = f"{name} {headline}"
      if all(keyword in search_text for keyword in keywords):
        return item.get("pk")

    return None

  def build_live_response(company_shortname: str, resolved_trip_type: str, date_value: str, group_size: int, headers: dict):
    item_pk = resolve_item_pk(company_shortname, resolved_trip_type, headers)
    if not item_pk:
      return None

    availabilities_url = (
      f"https://fareharbor.com/api/external/v1/companies/{company_shortname}"
      f"/items/{item_pk}/minimal/availabilities/date/{date_value}/?bookable_only=yes"
    )
    payload = fetch_json(availabilities_url, headers)
    availabilities = payload.get("availabilities", [])
    if not availabilities:
      return {
        "trip_type": resolved_trip_type,
        "requested_date": date_value,
        "party_size": group_size,
        "availability": [],
        "fits_any_option": False,
        "recommendation": "No online bookable departures were returned for that date. Offer nearby dates or human handoff.",
        "mock_data": False,
        "source": "fareharbor_external_api",
      }

    options = []
    for availability in availabilities:
      departure_time = format_time(availability["start_at"])
      status = availability.get("online_booking_status", "unknown")
      spots_left = availability.get("capacity")
      duration = "Unknown"
      if availability.get("start_at") and availability.get("end_at"):
        start_dt = datetime.strptime(availability["start_at"], "%Y-%m-%dT%H:%M:%S%z")
        end_dt = datetime.strptime(availability["end_at"], "%Y-%m-%dT%H:%M:%S%z")
        hours = max(1, round((end_dt - start_dt).total_seconds() / 3600))
        duration = f"About {hours} hour{'s' if hours != 1 else ''}"

      options.append({
        "departure_time": departure_time,
        "duration": duration,
        "status": status,
        "spots_left": spots_left,
        "availability_pk": availability.get("pk"),
        "booking_url": f"https://fareharbor.com/embeds/book/{company_shortname}/",
      })

    spots_known = all(option.get("spots_left") is not None for option in options)
    fits_any_option = any(group_size <= option["spots_left"] for option in options) if group_size > 0 and spots_known else True
    recommendation = ""
    if not fits_any_option:
      recommendation = "Group size appears larger than current online capacity. Offer alternate times or human handoff."

    return {
      "trip_type": resolved_trip_type,
      "requested_date": date_value,
      "party_size": group_size,
      "availability": options,
      "fits_any_option": fits_any_option,
      "recommendation": recommendation,
      "mock_data": False,
      "source": "fareharbor_external_api",
      "note": "Live FareHarbor External API result. Final booking and payment still occur in FareHarbor.",
    }

  def resolve_embed_item_pk(company_shortname: str, resolved_trip_type: str):
    env_key = f"FH_{resolved_trip_type.upper().replace(' ', '_')}_ITEM_PK"
    env_value = os.environ.get(env_key)
    if env_value and env_value.isdigit():
      return int(env_value)

    flow_id = os.environ.get("FH_EMBED_FLOW_ID", "1127725")
    flow_url = f"https://fareharbor.com/api/embed/{company_shortname}/flow-node/{flow_id}/v1/"
    payload = fetch_json(flow_url)
    children = payload.get("children", [])
    keywords = get_trip_keywords(resolved_trip_type)

    first_item_id = None
    for child in children:
      if child.get("type") != "item":
        continue

      item_id = child.get("id")
      if first_item_id is None and item_id:
        first_item_id = item_id

      heading = str(child.get("heading", "")).lower()
      subheading = str(child.get("subheading", "")).lower()
      search_text = f"{heading} {subheading}"
      if all(keyword in search_text for keyword in keywords):
        return item_id

    # Fallback for flows that only expose one item and fuzzy names.
    return first_item_id

  def build_embed_response(company_shortname: str, resolved_trip_type: str, date_value: str, group_size: int):
    item_pk = resolve_embed_item_pk(company_shortname, resolved_trip_type)
    if not item_pk:
      return None

    parsed_date = datetime.strptime(date_value, "%Y-%m-%d").date()
    month_url = (
      f"https://fareharbor.com/api/v1/companies/{company_shortname}/items/{item_pk}"
      f"/calendar/{parsed_date.year:04d}/{parsed_date.month:02d}/"
      "?allow_grouped=yes&bookable_only=no&asn=&path=1&is_fh_app=no"
    )
    payload = fetch_json(month_url)
    calendar = payload.get("calendar", {})
    weeks = calendar.get("weeks", [])

    day_entry = None
    for week in weeks:
      for day in week.get("days", []):
        if day.get("at") == date_value:
          day_entry = day
          break
      if day_entry:
        break

    if not day_entry:
      return None

    availabilities = day_entry.get("availabilities", [])
    if not availabilities:
      return {
        "trip_type": resolved_trip_type,
        "requested_date": date_value,
        "party_size": group_size,
        "availability": [],
        "fits_any_option": False,
        "recommendation": "No bookable departures were returned from the embed calendar for that date. Offer nearby dates or human handoff.",
        "mock_data": False,
        "source": "fareharbor_embed_api",
        "note": "Live no-key embed API lookup; endpoint and schema can change without notice.",
      }

    options = []
    for availability in availabilities:
      start_at = str(availability.get("start_at", ""))
      end_at = str(availability.get("end_at", ""))
      if not start_at:
        continue

      departure_time = format_time(start_at)
      duration = "Unknown"
      if end_at:
        try:
          start_dt = datetime.strptime(start_at, "%Y-%m-%dT%H:%M:%S")
          end_dt = datetime.strptime(end_at, "%Y-%m-%dT%H:%M:%S")
          hours = max(1, round((end_dt - start_dt).total_seconds() / 3600))
          duration = f"About {hours} hour{'s' if hours != 1 else ''}"
        except ValueError:
          pass

      is_bookable = bool(availability.get("is_bookable"))
      is_sold_out = bool(availability.get("is_sold_out"))
      approx_capacity = availability.get("approximate_available_capacity")
      status = "available" if is_bookable and not is_sold_out else "unavailable"

      book_path = str(availability.get("book_url", "")).strip()
      booking_url = f"https://fareharbor.com{book_path}" if book_path.startswith("/") else f"https://fareharbor.com/embeds/book/{company_shortname}/"

      options.append({
        "departure_time": departure_time,
        "duration": duration,
        "status": status,
        "spots_left": approx_capacity if isinstance(approx_capacity, int) and approx_capacity > 0 else None,
        "availability_pk": availability.get("pk"),
        "booking_url": booking_url,
      })

    if not options:
      return None

    spots_known = all(option.get("spots_left") is not None for option in options)
    fits_any_option = any(group_size <= option["spots_left"] for option in options) if group_size > 0 and spots_known else True
    recommendation = ""
    if not fits_any_option:
      recommendation = "Group size appears larger than current online capacity. Offer alternate times or human handoff."

    return {
      "trip_type": resolved_trip_type,
      "requested_date": date_value,
      "party_size": group_size,
      "availability": options,
      "fits_any_option": fits_any_option,
      "recommendation": recommendation,
      "mock_data": False,
      "source": "fareharbor_embed_api",
      "note": "Live no-key embed API lookup; endpoint and schema can change without notice.",
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
      "mock_data": True,
      "note": "Demo only. FareHarbor is the source of truth for final availability and booking.",
    }

  app_key = os.environ.get("FH_API_APP", "")
  user_key = os.environ.get("FH_API_USER", "")
  company_shortname = os.environ.get("FH_COMPANY_SHORTNAME", "sanctuarycruises")
  if app_key and user_key:
    headers = {
      "Accept": "application/json",
      "X-FareHarbor-API-App": app_key,
      "X-FareHarbor-API-User": user_key,
    }
    try:
      live_response = build_live_response(company_shortname, trip_key, requested_date, party_size, headers)
      if live_response:
        return live_response
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
      pass

  try:
    embed_response = build_embed_response(company_shortname, trip_key, requested_date, party_size)
    if embed_response:
      return embed_response
  except (HTTPError, URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
    pass

  if trip_key == "whale watching":
    data_file = Path(__file__).resolve().parents[1] / "data" / "whale_watch_schedule_next_3_months.json"
    if data_file.exists():
      try:
        schedule_data = json.loads(data_file.read_text(encoding="utf-8"))
        requested_dt = datetime.strptime(requested_date, "%Y-%m-%d")
        month_key = requested_dt.strftime("%Y-%m")
        date_label = f"{requested_dt.strftime('%A, %B')} {requested_dt.day}, {requested_dt.year}"
        month_schedule = schedule_data.get("months", {}).get(month_key, {})
        times = month_schedule.get(date_label)

        if times:
          options = []
          for time in times:
            options.append({
              "departure_time": time,
              "duration": "Up to 4 hours" if time in ("11:30 AM", "12:00 PM", "12:30 PM") else "Up to 3 hours",
              "status": "available (scraped snapshot)",
              "spots_left": None,
              "booking_url": "https://fareharbor.com/embeds/book/sanctuarycruises/?full-items=yes&flow=1127725",
            })

          return {
            "trip_type": trip_key,
            "requested_date": requested_date,
            "party_size": party_size,
            "availability": options,
            "fits_any_option": True,
            "recommendation": "Times are from a website snapshot. Confirm live seat counts in FareHarbor before booking.",
            "mock_data": True,
            "note": "Demo uses scraped website schedule snapshots for whale watching dates in June-August 2026.",
          }
      except Exception:
        # Fall back to static mock schedule if the date format is unknown or snapshot cannot be parsed.
        pass

  schedules = {
    "whale watching": [
      {
        "departure_time": "9:00 AM",
        "duration": "Up to 4 hours",
        "status": "available",
        "spots_left": 8,
      },
      {
        "departure_time": "1:30 PM",
        "duration": "Up to 4 hours",
        "status": "limited",
        "spots_left": 3,
      },
    ],
    "sunset cruise": [
      {
        "departure_time": "5:30 PM",
        "duration": "Up to 3 hours",
        "status": "available",
        "spots_left": 10,
      },
      {
        "departure_time": "6:15 PM",
        "duration": "Up to 3 hours",
        "status": "limited",
        "spots_left": 4,
      },
    ],
    "photography tour": [
      {
        "departure_time": "7:00 AM",
        "duration": "Up to 6 hours",
        "status": "limited",
        "spots_left": 5,
      },
      {
        "departure_time": "8:00 AM",
        "duration": "Up to 6 hours",
        "status": "available",
        "spots_left": 7,
      },
    ],
  }

  options = schedules[trip_key]
  for option in options:
    option["booking_url"] = "https://fareharbor.com/embeds/book/sanctuarycruises/"

  spots_known = all(option.get("spots_left") is not None for option in options)
  fits_any_option = any(party_size <= option["spots_left"] for option in options) if party_size > 0 and spots_known else True
  recommendation = ""
  if not fits_any_option:
    recommendation = "Party size exceeds current mock availability. Offer another departure or human handoff."

  return {
    "trip_type": trip_key,
    "requested_date": requested_date,
    "party_size": party_size,
    "availability": options,
    "fits_any_option": fits_any_option,
    "recommendation": recommendation,
    "mock_data": True,
    "note": "Demo only. FareHarbor is the source of truth for final availability, pricing, and booking confirmation.",
  }

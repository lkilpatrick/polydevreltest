from _gen import *  # <AUTO GENERATED>
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check_fareharbor_availability(conv: Conversation, flow: Flow):
    """
    Function step: read booking entities, call lookup_fareharbor_availability,
    store result on conv.state, return LLM context, and advance the flow.
    """

    # --- Read entities -------------------------------------------------------
    trip_type = (conv.entities.trip_type.value if conv.entities.trip_type else "whale watching")
    trip_date_raw = conv.entities.trip_date.value if conv.entities.trip_date else None
    adult_count = int(conv.entities.adult_count.value) if conv.entities.adult_count else 0
    child_count = int(conv.entities.child_count.value) if conv.entities.child_count else 0
    party_size = int(conv.entities.party_size.value) if conv.entities.party_size else (adult_count + child_count)
    if party_size == 0:
        party_size = adult_count + child_count

    # Normalise date to YYYY-MM-DD string
    requested_date = None
    if trip_date_raw:
        if isinstance(trip_date_raw, str) and len(trip_date_raw) >= 10:
            requested_date = trip_date_raw[:10]
        else:
            try:
                requested_date = datetime.strptime(str(trip_date_raw), "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                requested_date = str(trip_date_raw)

    if not requested_date:
        conv.state.fareharbor_result = None
        conv.log.warning("check_fareharbor_availability: no trip date available, cannot look up schedule")
        flow.goto_step("Collect Date", "Missing trip date")
        return "The caller has not yet provided a date. Ask for the desired trip date before checking availability."

    # --- Private charter short-circuit ----------------------------------------
    normalized_type = (trip_type or "").strip().lower()
    if any(kw in normalized_type for kw in ("private", "charter")):
        conv.state.fareharbor_result = {"human_required": True, "trip_type": "private charter"}
        conv.write_metric("BOOKING_INTENT", "private_charter")
        conv.exit_flow()
        return (
            "The caller wants a private charter. "
            "Tell them private charters require direct crew follow-up for logistics and pricing. "
            "Collect their name, contact phone or email, desired date, group size, and occasion if they haven't already shared it, "
            "then let them know the crew will be in touch. "
            "Phone: 831-917-1042. Email: crew@sanctuarycruises.com."
        )

    # --- Call live availability function -------------------------------------
    try:
        result = conv.functions.lookup_fareharbor_availability(
            trip_type=trip_type,
            requested_date=requested_date,
            adults=adult_count,
            children=child_count,
        )
    except Exception as exc:
        conv.log.error(f"check_fareharbor_availability: lookup failed: {exc}")
        result = None

    # --- Store result ---------------------------------------------------------
    booking_url = "https://fareharbor.com/embeds/book/sanctuarycruises/?flow=1127712&full-items=yes"
    if result:
        conv.state.fareharbor_result = json.dumps(result) if not isinstance(result, str) else result
        if isinstance(result, dict) and result.get("booking_url"):
            booking_url = result["booking_url"]
    else:
        conv.state.fareharbor_result = None

    conv.state.booking_url = booking_url
    conv.write_metric("BOOKING_INTENT", "availability_checked")

    # --- Build LLM context ---------------------------------------------------
    if not result:
        conv.exit_flow()
        return (
            f"Live availability could not be retrieved right now. "
            f"Tell the caller that they can confirm availability and book directly through FareHarbor. "
            f"The booking link is sanctuarycruises.com or they can call 831-917-1042. "
            f"Do not claim any booking is confirmed."
        )

    if isinstance(result, dict):
        source = result.get("source", "unknown")
        is_fallback = result.get("fallback_data", False)
        options = result.get("availability", [])
        fits_any = result.get("fits_any_option", False)
        human_required = result.get("human_required", False)

        if human_required:
            conv.exit_flow()
            return (
                "Escalate to crew for this request. "
                "Phone: 831-917-1042. Email: crew@sanctuarycruises.com."
            )

        if not options:
            conv.exit_flow()
            return (
                f"No departures were found for {trip_type} on {requested_date}. "
                f"Suggest the caller try a nearby date or call 831-917-1042 to check directly. "
                f"Do not say the date is unavailable unless you are certain — FareHarbor is the source of truth."
            )

        times = ", ".join(opt.get("departure_time", "") for opt in options if opt.get("departure_time"))
        spots_info = ""
        if options[0].get("spots_left"):
            spots_info = f" Available spots on first departure: {options[0]['spots_left']}."

        freshness_note = ""
        if is_fallback:
            freshness_note = " Note: this comes from a recent schedule snapshot, not a live FareHarbor query — advise the caller to confirm seat counts before booking."
        elif source == "fareharbor_embed_api":
            freshness_note = " Source is live FareHarbor embed calendar."
        elif source == "fareharbor_external_api":
            freshness_note = " Source is live FareHarbor External API."

        fit_note = ""
        if not fits_any and party_size > 0:
            fit_note = f" Party size of {party_size} may exceed online availability — offer another departure or crew handoff."

        conv.exit_flow()
        return (
            f"Availability found for {trip_type} on {requested_date}. "
            f"Departure times: {times}.{spots_info}{fit_note}"
            f"{freshness_note} "
            f"Tell the caller the times and that FareHarbor is the source of truth for final pricing and seat confirmation. "
            f"Do not say the booking is confirmed. "
            f"Offer them the booking link or crew phone number to complete the reservation."
        )

    # Fallthrough — unknown result shape
    conv.exit_flow()
    return (
        "Availability data was returned but could not be parsed. "
        "Tell the caller to confirm directly through FareHarbor or call 831-917-1042."
    )

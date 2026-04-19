from __future__ import annotations

import json
from typing import Any

import requests


SERPAPI_URL = "https://serpapi.com/search"
REQUEST_TIMEOUT_SECONDS = 45


class SerpApiError(Exception):
    """Raised when the SerpAPI request or response is invalid."""


def search_flights(
    api_key: str,
    origin: str,
    destination: str,
    departure_date: str,
    passengers: int,
    currency: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = fetch_flights(
        api_key=api_key,
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        passengers=passengers,
        currency=currency,
    )
    normalized_rows = normalize_flight_rows(
        api_key=api_key,
        payload=payload,
        currency=currency,
        trip_type="one_way",
        requested_legs=[{"origin": origin, "destination": destination, "departure_date": departure_date}],
    )
    return payload, normalized_rows


def search_multi_city_flights(
    api_key: str,
    legs: list[dict[str, str]],
    passengers: int,
    currency: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = fetch_multi_city_flights(
        api_key=api_key,
        legs=legs,
        passengers=passengers,
        currency=currency,
    )
    normalized_rows = normalize_flight_rows(
        api_key=api_key,
        payload=payload,
        currency=currency,
        trip_type="multi_city",
        requested_legs=legs,
    )
    return payload, normalized_rows


def fetch_flights(
    api_key: str,
    origin: str,
    destination: str,
    departure_date: str,
    passengers: int,
    currency: str,
) -> dict[str, Any]:
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": departure_date,
        "currency": currency,
        "type": "2",
        "adults": str(passengers),
        "deep_search": "true",
        "hl": "en",
        "gl": "us",
        "api_key": api_key,
    }

    try:
        response = requests.get(SERPAPI_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise SerpApiError(f"Could not reach SerpAPI: {exc}") from exc

    if response.status_code != 200:
        raise SerpApiError(f"SerpAPI returned HTTP {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise SerpApiError("SerpAPI returned a non-JSON response.") from exc

    if payload.get("error"):
        raise SerpApiError(str(payload["error"]))

    return payload


def fetch_multi_city_flights(
    api_key: str,
    legs: list[dict[str, str]],
    passengers: int,
    currency: str,
) -> dict[str, Any]:
    params = {
        "engine": "google_flights",
        "type": "3",
        "multi_city_json": json.dumps(
            [
                {
                    "departure_id": leg["origin"],
                    "arrival_id": leg["destination"],
                    "date": leg["departure_date"],
                }
                for leg in legs
            ]
        ),
        "currency": currency,
        "adults": str(passengers),
        "deep_search": "true",
        "hl": "en",
        "gl": "us",
        "api_key": api_key,
    }

    try:
        response = requests.get(SERPAPI_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise SerpApiError(f"Could not reach SerpAPI: {exc}") from exc

    if response.status_code != 200:
        raise SerpApiError(f"SerpAPI returned HTTP {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise SerpApiError("SerpAPI returned a non-JSON response.") from exc

    if payload.get("error"):
        raise SerpApiError(str(payload["error"]))

    return payload


def normalize_flight_rows(
    api_key: str,
    payload: dict[str, Any],
    currency: str,
    trip_type: str,
    requested_legs: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for section_name in ("best_flights", "other_flights"):
        for result_index, group in enumerate(payload.get(section_name, []), start=1):
            flights = group.get("flights", [])
            itinerary_legs = build_itinerary_legs(flights, requested_legs or [])
            booking_provider, booking_link = fetch_booking_details(
                api_key=api_key,
                booking_token=group.get("booking_token"),
                currency=currency,
            )
            rows.append(
                {
                    "trip_type": trip_type,
                    "source_section": section_name,
                    "result_index": result_index,
                    "price": group.get("price"),
                    "price_display": format_price(group.get("price"), currency),
                    "airlines": collect_airlines(flights),
                    "route_summary": build_route_summary(itinerary_legs, flights),
                    "departure_airports": join_values(
                        flight.get("departure_airport", {}).get("id") for flight in flights
                    ),
                    "arrival_airports": join_values(
                        flight.get("arrival_airport", {}).get("id") for flight in flights
                    ),
                    "departure_times": join_values(
                        flight.get("departure_airport", {}).get("time") for flight in flights
                    ),
                    "arrival_times": join_values(
                        flight.get("arrival_airport", {}).get("time") for flight in flights
                    ),
                    "duration": format_duration(group.get("total_duration")),
                    "stops": format_stops(flights),
                    "itinerary_legs": itinerary_legs,
                    "booking_provider": booking_provider,
                    "booking_link": booking_link,
                }
            )

    return rows


def fetch_booking_details(
    api_key: str,
    booking_token: str | None,
    currency: str,
) -> tuple[str | None, str | None]:
    if not booking_token:
        return None, None

    params = {
        "engine": "google_flights",
        "booking_token": booking_token,
        "currency": currency,
        "hl": "en",
        "gl": "us",
        "api_key": api_key,
    }

    try:
        response = requests.get(SERPAPI_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None, None

    option = next(iter(payload.get("booking_options", [])), None)
    if not option:
        return None, None

    together = option.get("together", {})
    if together:
        provider = together.get("book_with")
        request_info = together.get("booking_request", {})
        direct_url = request_info.get("url") if not request_info.get("post_data") else None
        return provider, direct_url

    for leg_name in ("departing", "returning"):
        leg = option.get(leg_name, {})
        if not leg:
            continue
        provider = leg.get("book_with")
        request_info = leg.get("booking_request", {})
        direct_url = request_info.get("url") if not request_info.get("post_data") else None
        if provider or direct_url:
            return provider, direct_url

    return None, None


def collect_airlines(flights: list[dict[str, Any]]) -> str | None:
    airlines: list[str] = []
    for flight in flights:
        airline = flight.get("airline")
        if airline and airline not in airlines:
            airlines.append(airline)
    return ", ".join(airlines) if airlines else None


def build_itinerary_legs(
    flights: list[dict[str, Any]],
    requested_legs: list[dict[str, str]],
) -> list[dict[str, Any]]:
    if not flights:
        return []

    if not requested_legs:
        return [build_leg_summary(flights, 1)]

    itinerary_legs: list[dict[str, Any]] = []
    current_segments: list[dict[str, Any]] = []
    current_leg_index = 0

    for flight in flights:
        current_segments.append(flight)
        if current_leg_index >= len(requested_legs):
            continue

        expected_destination = requested_legs[current_leg_index].get("destination")
        actual_destination = flight.get("arrival_airport", {}).get("id")
        if actual_destination == expected_destination:
            itinerary_legs.append(build_leg_summary(current_segments, current_leg_index + 1))
            current_segments = []
            current_leg_index += 1

    if current_segments:
        itinerary_legs.append(build_leg_summary(current_segments, current_leg_index + 1))

    return itinerary_legs


def build_leg_summary(segments: list[dict[str, Any]], leg_number: int) -> dict[str, Any]:
    first_segment = segments[0]
    last_segment = segments[-1]
    airlines = collect_airlines(segments)
    return {
        "leg_number": leg_number,
        "route": (
            f"{first_segment.get('departure_airport', {}).get('id', 'Unknown')} -> "
            f"{last_segment.get('arrival_airport', {}).get('id', 'Unknown')}"
        ),
        "departure_time": first_segment.get("departure_airport", {}).get("time"),
        "arrival_time": last_segment.get("arrival_airport", {}).get("time"),
        "airlines": airlines,
        "stops": format_stops(segments),
        "segments": [
            {
                "route": (
                    f"{segment.get('departure_airport', {}).get('id', 'Unknown')} -> "
                    f"{segment.get('arrival_airport', {}).get('id', 'Unknown')}"
                ),
                "departure_time": segment.get("departure_airport", {}).get("time"),
                "arrival_time": segment.get("arrival_airport", {}).get("time"),
                "airline": segment.get("airline"),
                "flight_number": segment.get("flight_number"),
                "duration": format_duration(segment.get("duration")),
            }
            for segment in segments
        ],
    }


def build_route_summary(
    itinerary_legs: list[dict[str, Any]],
    flights: list[dict[str, Any]],
) -> str | None:
    if itinerary_legs:
        return " | ".join(str(leg.get("route")) for leg in itinerary_legs if leg.get("route"))

    if not flights:
        return None

    start = flights[0].get("departure_airport", {}).get("id")
    end = flights[-1].get("arrival_airport", {}).get("id")
    if start and end:
        return f"{start} -> {end}"
    return None


def join_values(values: Any) -> str | None:
    cleaned = [value for value in values if value]
    return " | ".join(cleaned) if cleaned else None


def format_duration(total_minutes: int | None) -> str | None:
    if total_minutes is None:
        return None

    hours, minutes = divmod(int(total_minutes), 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def format_stops(flights: list[dict[str, Any]]) -> str:
    stop_count = max(len(flights) - 1, 0)
    if stop_count == 0:
        return "Nonstop"
    if stop_count == 1:
        return "1 stop"
    return f"{stop_count} stops"


def format_price(price: int | float | None, currency: str) -> str | None:
    if price is None:
        return None
    return f"{currency} {price}"

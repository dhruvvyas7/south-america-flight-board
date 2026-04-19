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
    normalized_rows = normalize_flight_rows(api_key=api_key, payload=payload, currency=currency)
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
    normalized_rows = normalize_flight_rows(api_key=api_key, payload=payload, currency=currency)
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
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for section_name in ("best_flights", "other_flights"):
        for result_index, group in enumerate(payload.get(section_name, []), start=1):
            flights = group.get("flights", [])
            booking_provider, booking_link = fetch_booking_details(
                api_key=api_key,
                booking_token=group.get("booking_token"),
                currency=currency,
            )
            rows.append(
                {
                    "source_section": section_name,
                    "result_index": result_index,
                    "price": group.get("price"),
                    "price_display": format_price(group.get("price"), currency),
                    "airlines": collect_airlines(flights),
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

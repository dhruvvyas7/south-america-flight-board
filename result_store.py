from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def save_search_results(
    results_dir: str,
    search_params: dict[str, Any],
    raw_payload: dict[str, Any],
    normalized_rows: list[dict[str, Any]],
) -> tuple[str, str]:
    target_dir = Path(results_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_stub = build_filename_stub(search_params)
    json_path = target_dir / f"{timestamp}_{filename_stub}.json"
    csv_path = target_dir / f"{timestamp}_{filename_stub}.csv"

    json_content = {
        "saved_at": datetime.now().isoformat(),
        "search_params": search_params,
        "results": normalized_rows,
        "raw_payload": raw_payload,
    }
    json_path.write_text(json.dumps(json_content, indent=2), encoding="utf-8")

    fieldnames = [
        "trip_type",
        "requested_route_summary",
        "requested_dates_summary",
        "source_section",
        "result_index",
        "price",
        "price_display",
        "airlines",
        "route_summary",
        "layover_summary",
        "departure_airports",
        "arrival_airports",
        "departure_times",
        "arrival_times",
        "duration",
        "stops",
        "itinerary_legs_json",
        "source_detail_scope",
        "booking_provider",
        "booking_link",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in normalized_rows:
            writer.writerow(build_csv_row(row))

    return str(json_path), str(csv_path)


def build_filename_stub(search_params: dict[str, Any]) -> str:
    if search_params.get("search_mode") == "multi_city":
        legs = search_params.get("legs", [])
        if legs:
            first_origin = str(legs[0].get("origin", "trip"))
            last_destination = str(legs[-1].get("destination", "trip"))
            return sanitize_filename_part(f"multi_{first_origin}_{last_destination}")
        return "multi_trip"

    origin = str(search_params.get("origin", "unknown_origin"))
    destination = str(search_params.get("destination", "unknown_destination"))
    return sanitize_filename_part(f"{origin}_{destination}")


def sanitize_filename_part(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
    return cleaned.strip("_") or "results"


def build_csv_row(row: dict[str, Any]) -> dict[str, Any]:
    csv_row = dict(row)
    itinerary_legs = csv_row.pop("itinerary_legs", None)
    csv_row["itinerary_legs_json"] = json.dumps(itinerary_legs, ensure_ascii=True) if itinerary_legs else ""
    return csv_row

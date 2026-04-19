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
    origin = search_params["origin"]
    destination = search_params["destination"]
    json_path = target_dir / f"{timestamp}_{origin}_{destination}.json"
    csv_path = target_dir / f"{timestamp}_{origin}_{destination}.csv"

    json_content = {
        "saved_at": datetime.now().isoformat(),
        "search_params": search_params,
        "results": normalized_rows,
        "raw_payload": raw_payload,
    }
    json_path.write_text(json.dumps(json_content, indent=2), encoding="utf-8")

    fieldnames = [
        "source_section",
        "result_index",
        "price",
        "price_display",
        "airlines",
        "departure_airports",
        "arrival_airports",
        "departure_times",
        "arrival_times",
        "duration",
        "stops",
        "booking_provider",
        "booking_link",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in normalized_rows:
            writer.writerow(row)

    return str(json_path), str(csv_path)

from __future__ import annotations

import os
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from airport_options import AIRPORT_CODE_BY_LABEL, AIRPORT_LABELS, SOUTH_AMERICA_PRESET
from result_store import save_search_results
from serpapi_client import SerpApiError, search_flights, search_multi_city_flights


load_dotenv()

st.set_page_config(
    page_title="South America Flight Board",
    layout="wide",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 207, 107, 0.35), transparent 28%),
                radial-gradient(circle at top right, rgba(18, 138, 167, 0.28), transparent 24%),
                linear-gradient(180deg, #fff9ef 0%, #f5fbff 48%, #eef8f2 100%);
        }
        .hero-card {
            background: linear-gradient(135deg, #0b6e4f 0%, #17836c 45%, #f4a261 100%);
            border-radius: 24px;
            color: white;
            padding: 1.6rem 1.7rem;
            box-shadow: 0 18px 48px rgba(11, 110, 79, 0.22);
            margin-bottom: 1rem;
        }
        .hero-card h1 {
            margin: 0 0 0.35rem 0;
            font-size: 3rem;
            line-height: 1;
        }
        .hero-card p {
            margin: 0.2rem 0;
            font-size: 1rem;
        }
        .trip-chip-row {
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
            margin-top: 0.8rem;
        }
        .trip-chip {
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.24);
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            font-size: 0.92rem;
        }
        .section-card {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(11, 110, 79, 0.08);
            border-radius: 22px;
            padding: 1rem 1rem 0.4rem 1rem;
            box-shadow: 0 12px 30px rgba(46, 72, 98, 0.08);
            margin-bottom: 1rem;
        }
        .section-label {
            font-size: 0.82rem;
            font-weight: 700;
            color: #0b6e4f;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }
        .tiny-note {
            color: #51616f;
            font-size: 0.95rem;
            margin-bottom: 0.7rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(11, 110, 79, 0.09);
            padding: 0.7rem;
            border-radius: 16px;
        }
        .result-banner {
            background: linear-gradient(135deg, rgba(255, 224, 170, 0.7), rgba(173, 230, 210, 0.7));
            border-radius: 18px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.8rem;
            border: 1px solid rgba(11, 110, 79, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_api_key() -> str | None:
    api_key = os.getenv("SERPAPI_API_KEY")
    if api_key:
        return api_key

    try:
        return st.secrets.get("SERPAPI_API_KEY")
    except Exception:
        return None


def default_date(offset_days: int) -> date:
    return date.today() + timedelta(days=offset_days)


def init_state() -> None:
    defaults = {
        "search_mode": "One-way",
        "entry_mode": "Pick from list",
        "currency": "CAD",
        "passengers": 1,
        "origin_airport_label": "Montreal, Canada (YUL)",
        "destination_airport_label": "Bogota, Colombia (BOG)",
        "origin_manual": "",
        "destination_manual": "",
        "departure_date": default_date(30),
        "leg_1_origin": "Montreal, Canada (YUL)",
        "leg_1_destination": "Bogota, Colombia (BOG)",
        "leg_1_date": date(2026, 11, 8),
        "leg_2_origin": "Bogota, Colombia (BOG)",
        "leg_2_destination": "Quito, Ecuador (UIO)",
        "leg_2_date": date(2026, 11, 11),
        "leg_3_origin": "Quito, Ecuador (UIO)",
        "leg_3_destination": "Cusco, Peru (CUZ)",
        "leg_3_date": date(2026, 11, 14),
        "leg_4_origin": "Cusco, Peru (CUZ)",
        "leg_4_destination": "Montreal, Canada (YUL)",
        "leg_4_date": date(2026, 11, 19),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def apply_south_america_preset() -> None:
    preset = SOUTH_AMERICA_PRESET
    st.session_state.search_mode = "Multi-city"
    st.session_state.entry_mode = "Pick from list"
    st.session_state.currency = preset["currency"]
    st.session_state.passengers = preset["passengers"]
    st.session_state.origin_airport_label = preset["one_way_origin"]
    st.session_state.destination_airport_label = preset["one_way_destination"]
    st.session_state.departure_date = date.fromisoformat(preset["one_way_date"])

    for index, leg in enumerate(preset["legs"], start=1):
        st.session_state[f"leg_{index}_origin"] = leg["origin_label"]
        st.session_state[f"leg_{index}_destination"] = leg["destination_label"]
        st.session_state[f"leg_{index}_date"] = date.fromisoformat(leg["date"])


def render_value(value: str | None) -> str:
    return value if value else "Not available"


def airport_input(
    label: str,
    label_key: str,
    manual_key: str,
    entry_mode: str,
    help_text: str,
) -> str:
    if entry_mode == "Pick from list":
        selected_label = st.selectbox(
            label,
            AIRPORT_LABELS,
            key=label_key,
            help=help_text,
        )
        return AIRPORT_CODE_BY_LABEL[selected_label]

    typed_value = st.text_input(
        label,
        key=manual_key,
        help="Type a 3-letter airport code like YUL, BOG, LIM, or EZE.",
        max_chars=10,
    )
    return typed_value.strip().upper()


def validate_code(code: str, field_name: str) -> None:
    if not code:
        raise SerpApiError(f"{field_name} is required.")
    if len(code) < 3:
        raise SerpApiError(f"{field_name} should be a 3-letter airport code like YUL or BOG.")


def validate_currency(currency_code: str) -> None:
    if not currency_code:
        raise SerpApiError("Currency is required.")
    if len(currency_code) != 3:
        raise SerpApiError("Currency should be a 3-letter code like CAD, USD, or EUR.")


def render_results(
    normalized_rows: list[dict[str, str | int | None]],
    raw_payload: dict,
    json_path: str,
    csv_path: str,
    heading: str,
) -> None:
    st.success(f"Saved results to `{json_path}` and `{csv_path}`.")
    st.markdown(
        f"""
        <div class="result-banner">
            <strong>{heading}</strong><br>
            {len(normalized_rows)} result(s) came back. No rankings, no opinions, just the raw flight board.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for idx, row in enumerate(normalized_rows, start=1):
        with st.container(border=True):
            title_col, price_col = st.columns([4, 1])
            with title_col:
                st.markdown(
                    f"**{idx}. {render_value(row['airlines'])}**"
                    f"  \n{render_value(row['departure_airports'])} -> "
                    f"{render_value(row['arrival_airports'])}"
                )
            with price_col:
                st.metric("Price", render_value(row["price_display"]))

            info_col1, info_col2, info_col3 = st.columns(3)
            with info_col1:
                st.write(f"Departure: {render_value(row['departure_times'])}")
                st.write(f"Arrival: {render_value(row['arrival_times'])}")
            with info_col2:
                st.write(f"Duration: {render_value(row['duration'])}")
                st.write(f"Stops: {render_value(row['stops'])}")
            with info_col3:
                st.write(f"Source section: {render_value(row['source_section'])}")
                st.write(f"Booking seller: {render_value(row['booking_provider'])}")

            booking_link = row.get("booking_link")
            if booking_link:
                st.link_button("Open booking link", booking_link, use_container_width=False)
            else:
                st.write("Booking link: Not available")

    with st.expander("Raw API response"):
        st.json(raw_payload)


inject_styles()
init_state()

st.markdown(
    """
    <div class="hero-card">
        <h1>South America Flight Board</h1>
        <p>Trip planning, but with fewer spreadsheets and only a little healthy airport drama.</p>
        <p>Search one-way routes or stitch together a multi-city run across the continent.</p>
        <div class="trip-chip-row">
            <div class="trip-chip">Beginner-friendly airport picker</div>
            <div class="trip-chip">One-way and multi-city</div>
            <div class="trip-chip">Raw results only</div>
            <div class="trip-chip">JSON and CSV exports</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

toolbar_left, toolbar_right = st.columns([3, 1])
with toolbar_left:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-label">How It Works</div>
            <div class="tiny-note">
                Pick airports from the list if you want the easy version. Use manual mode if you already know the codes.
                The South America preset loads your current itinerary, and when you ignore the preset this behaves like a normal flight checker.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with toolbar_right:
    if st.button("Load South America preset", use_container_width=True):
        apply_south_america_preset()
        st.rerun()

st.radio(
    "Search type",
    ["One-way", "Multi-city"],
    horizontal=True,
    key="search_mode",
)

st.radio(
    "Airport input style",
    ["Pick from list", "Type airport code"],
    horizontal=True,
    key="entry_mode",
)

shared_left, shared_right = st.columns([1, 1])
with shared_left:
    st.text_input(
        "Currency",
        key="currency",
        help="Example: CAD, USD, EUR",
        max_chars=3,
    )
with shared_right:
    st.number_input(
        "Passengers",
        key="passengers",
        min_value=1,
        max_value=9,
        step=1,
    )

if st.session_state.search_mode == "One-way":
    st.markdown(
        """
        <div class="section-card">
            <div class="section-label">One-Way Search</div>
            <div class="tiny-note">Perfect for checking one leg at a time before the itinerary gets ambitious.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("one_way_form"):
        col1, col2 = st.columns(2)
        with col1:
            origin_code = airport_input(
                "Origin airport",
                "origin_airport_label",
                "origin_manual",
                st.session_state.entry_mode,
                "Pick a city-airport combo from the list, or switch to manual mode for codes.",
            )
            departure_date = st.date_input(
                "Departure date",
                key="departure_date",
                min_value=date.today(),
            )
        with col2:
            destination_code = airport_input(
                "Destination airport",
                "destination_airport_label",
                "destination_manual",
                st.session_state.entry_mode,
                "Pick a city-airport combo from the list, or switch to manual mode for codes.",
            )

        one_way_submitted = st.form_submit_button("Search one-way flights", use_container_width=True)

    if one_way_submitted:
        api_key = load_api_key()
        if not api_key:
            st.error(
                "Missing API key. Add `SERPAPI_API_KEY` to your `.env` file for local use, "
                "or to Streamlit secrets for deployment."
            )
            st.stop()

        currency_code = st.session_state.currency.strip().upper()
        try:
            validate_code(origin_code, "Origin airport")
            validate_code(destination_code, "Destination airport")
            validate_currency(currency_code)

            raw_payload, normalized_rows = search_flights(
                api_key=api_key,
                origin=origin_code,
                destination=destination_code,
                departure_date=departure_date.isoformat(),
                passengers=int(st.session_state.passengers),
                currency=currency_code,
            )
        except SerpApiError as exc:
            st.error(f"Search failed: {exc}")
            st.stop()
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
            st.stop()

        if not normalized_rows:
            st.warning("No flight results were returned for this search.")
            st.json(raw_payload)
            st.stop()

        search_params = {
            "search_mode": "one_way",
            "origin": origin_code,
            "destination": destination_code,
            "departure_date": departure_date.isoformat(),
            "passengers": int(st.session_state.passengers),
            "currency": currency_code,
        }
        json_path, csv_path = save_search_results(
            results_dir="results",
            search_params=search_params,
            raw_payload=raw_payload,
            normalized_rows=normalized_rows,
        )
        render_results(
            normalized_rows=normalized_rows,
            raw_payload=raw_payload,
            json_path=json_path,
            csv_path=csv_path,
            heading="One-way flight board",
        )

else:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-label">Multi-City Search</div>
            <div class="tiny-note">
                Build the trip leg by leg. After loading the preset, you can freely change any airport or date below.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("multi_city_form"):
        legs: list[dict[str, str]] = []
        for index in range(1, 5):
            st.markdown(f"**Leg {index}**")
            leg_col1, leg_col2, leg_col3 = st.columns([1.2, 1.2, 1])
            with leg_col1:
                leg_origin = airport_input(
                    f"Origin for leg {index}",
                    f"leg_{index}_origin",
                    f"leg_{index}_origin_manual",
                    st.session_state.entry_mode,
                    "Use the list for fast setup or manual mode for airport codes.",
                )
            with leg_col2:
                leg_destination = airport_input(
                    f"Destination for leg {index}",
                    f"leg_{index}_destination",
                    f"leg_{index}_destination_manual",
                    st.session_state.entry_mode,
                    "Use the list for fast setup or manual mode for airport codes.",
                )
            with leg_col3:
                leg_date = st.date_input(
                    f"Date for leg {index}",
                    key=f"leg_{index}_date",
                    min_value=date.today(),
                )

            legs.append(
                {
                    "origin": leg_origin,
                    "destination": leg_destination,
                    "departure_date": leg_date.isoformat(),
                }
            )

        multi_city_submitted = st.form_submit_button("Search multi-city flights", use_container_width=True)

    if multi_city_submitted:
        api_key = load_api_key()
        if not api_key:
            st.error(
                "Missing API key. Add `SERPAPI_API_KEY` to your `.env` file for local use, "
                "or to Streamlit secrets for deployment."
            )
            st.stop()

        currency_code = st.session_state.currency.strip().upper()
        try:
            validate_currency(currency_code)
            for leg_index, leg in enumerate(legs, start=1):
                validate_code(leg["origin"], f"Origin for leg {leg_index}")
                validate_code(leg["destination"], f"Destination for leg {leg_index}")

            raw_payload, normalized_rows = search_multi_city_flights(
                api_key=api_key,
                legs=legs,
                passengers=int(st.session_state.passengers),
                currency=currency_code,
            )
        except SerpApiError as exc:
            st.error(f"Search failed: {exc}")
            st.stop()
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
            st.stop()

        if not normalized_rows:
            st.warning("No flight results were returned for this itinerary.")
            st.json(raw_payload)
            st.stop()

        search_params = {
            "search_mode": "multi_city",
            "legs": legs,
            "passengers": int(st.session_state.passengers),
            "currency": currency_code,
        }
        json_path, csv_path = save_search_results(
            results_dir="results",
            search_params=search_params,
            raw_payload=raw_payload,
            normalized_rows=normalized_rows,
        )
        render_results(
            normalized_rows=normalized_rows,
            raw_payload=raw_payload,
            json_path=json_path,
            csv_path=csv_path,
            heading="Multi-city flight board",
        )

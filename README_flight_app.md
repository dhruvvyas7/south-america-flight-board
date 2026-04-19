# Streamlit Flight Search App

A public-facing Streamlit app that searches flights with SerpAPI, shows the raw results in a simple UI, and saves every search to the local `results/` folder as JSON and CSV.

## Files

- `app.py`: Streamlit app
- `serpapi_client.py`: SerpAPI request and response normalization helpers
- `result_store.py`: JSON and CSV export helpers
- `airport_options.py`: friendly airport labels and South America presets
- `requirements.txt`: Python dependencies
- `.env.example`: local environment variable example
- `results/`: saved search output folder

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Add your real `SERPAPI_API_KEY` to `.env`.
5. Run the Streamlit app.

## Streamlit Community Cloud

For local development, the app reads `SERPAPI_API_KEY` from `.env`.

For Streamlit Community Cloud deployment:

1. Push these app files to a GitHub repo.
2. In Streamlit Community Cloud, point the app to `app.py`.
3. Add `SERPAPI_API_KEY` in the app's Secrets settings.

The app will use Streamlit secrets automatically when `.env` is not available.

## Notes

- The app supports both one-way and multi-city searches.
- Airport selection is beginner-friendly with city-and-airport labels for common routes, plus manual code entry when needed.
- The app does not rank or recommend flights.
- Booking links are shown only when SerpAPI returns a direct booking URL.
- Each flight result may trigger an extra booking-options lookup when a booking token is available.

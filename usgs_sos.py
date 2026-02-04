import requests
import pandas as pd
from datetime import datetime

# ==========================
# Fetch Earthquake Data
# ==========================
def fetch_usgs_data():
    """
    Fetch global earthquake data for the last 24 hours from USGS.
    """
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    print("[USGS] Fetching earthquake data...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[USGS] Error fetching data: {e}")
        return pd.DataFrame()

    quakes = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        # Extract data safely
        magnitude = props.get("mag")
        place = props.get("place", "Unknown location")
        timestamp = props.get("time")
        depth = geometry.get("coordinates", [None, None, None])[2]

        # Convert timestamp to datetime
        quake_time = datetime.utcfromtimestamp(timestamp / 1000) if timestamp else None

        quakes.append({
            "Source": "USGS",
            "Content": f"M{magnitude} earthquake - {place}",
            "Subreddit": None,
            "Author": None,
            "Score": magnitude,
            "Num_Comments": depth,  # repurposed for quake depth
            "Created_At": quake_time
        })

    return pd.DataFrame(quakes)

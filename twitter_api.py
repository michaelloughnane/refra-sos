import os
import time
import tweepy
import pandas as pd
import requests
from datetime import datetime
from tweepy import Paginator

# ==========================
# CONFIGURATION
# ==========================
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "YOUR_TWITTER_BEARER_TOKEN")
SEARCH_QUERY = "earthquake -is:retweet lang:en"  # filter retweets, only English
MAX_PAGES = 3  # prevent overuse and hitting rate limits
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

# ==========================
# TWITTER CLIENT SETUP
# ==========================
def authenticate_twitter():
    """Authenticate using Twitter API v2."""
    try:
        client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
        print(f"Authenticated. tweepy client type: {type(client)}")
        return client
    except Exception as e:
        print(f"Error authenticating Twitter client: {e}")
        return None


# ==========================
# FETCH TWEETS
# ==========================
def fetch_tweets(client, query, max_pages=MAX_PAGES):
    """
    Fetch tweets using pagination safely.
    Each page = up to 100 tweets.
    """
    all_tweets = []

    paginator = Paginator(
        client.search_recent_tweets,
        query=query,
        tweet_fields=["created_at", "public_metrics", "lang"],
        user_fields=["location", "username"],
        expansions=["author_id"],
        max_results=100  # max allowed per page
    )

    for page_number, page in enumerate(paginator, start=1):
        print(f"Fetching page {page_number}...")

        if not page.data:
            print("No more tweets found.")
            break

        for tweet in page.data:
            metrics = tweet.public_metrics or {}
            all_tweets.append({
                "Source": "Twitter",
                "Content": tweet.text,
                "Created At": tweet.created_at,
                "Likes": metrics.get("like_count", 0),
                "Retweets": metrics.get("retweet_count", 0),
            })

        # Stop early to prevent exceeding plan limit
        if page_number >= max_pages:
            print(f"Reached max page limit ({max_pages}). Stopping pagination.")
            break

    return pd.DataFrame(all_tweets)


# ==========================
# FETCH USGS DATA (FALLBACK)
# ==========================
def fetch_usgs_data():
    """
    Fetch earthquake data globally from USGS.
    Returns earthquakes from the past 24 hours.
    """
    print("Fetching USGS earthquake data...")
    try:
        response = requests.get(USGS_URL)
        response.raise_for_status()
        data = response.json()

        quakes = []
        for feature in data["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            quakes.append({
                "Source": "USGS",
                "Magnitude": props.get("mag"),
                "Place": props.get("place"),
                "Time": datetime.utcfromtimestamp(props["time"] / 1000),
                "Depth (km)": coords[2],
                "Longitude": coords[0],
                "Latitude": coords[1],
            })
        return pd.DataFrame(quakes)
    except Exception as e:
        print(f"Error fetching USGS data: {e}")
        return pd.DataFrame()


# ==========================
# SAFE FETCH FUNCTION
# ==========================
def safe_fetch_tweets_or_usgs(client, query):
    """
    Attempts to fetch tweets first.
    Falls back to USGS data if Twitter limit is exceeded or an error occurs.
    """
    try:
        tweets_df = fetch_tweets(client, query)
        if tweets_df.empty:
            raise Exception("No tweets retrieved. Switching to USGS fallback.")
        print(f"Successfully fetched {len(tweets_df)} tweets from Twitter.")
        return tweets_df
    except Exception as e:
        print(f"Twitter error: {e}")
        print("Switching to USGS fallback...")
        usgs_df = fetch_usgs_data()
        print(f"Fetched {len(usgs_df)} earthquake records from USGS.")
        return usgs_df


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    twitter_client = authenticate_twitter()

    if not twitter_client:
        print("Twitter authentication failed. Using USGS data only.")
        final_df = fetch_usgs_data()
    else:
        final_df = safe_fetch_tweets_or_usgs(twitter_client, SEARCH_QUERY)

    # Display data
    print("\nFinal Data Preview:")
    print(final_df.head())

    # Save to CSV for later analysis
    output_file = "earthquake_data.csv"
    final_df.to_csv(output_file, index=False)
    print(f"\nData saved to {output_file}")

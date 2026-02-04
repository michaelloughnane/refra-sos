import os
import time
import tweepy
import pandas as pd
from tweepy import Paginator
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# ==========================
# Twitter Authentication
# ==========================
def authenticate_twitter():
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError("Missing TWITTER_BEARER_TOKEN environment variable.")

    try:
        client = tweepy.Client(bearer_token=bearer_token)
        print("Twitter authentication successful.")
        return client
    except Exception as e:
        print(f"Error authenticating Twitter client: {e}")
        return None


# ==========================
# Fetch Tweets
# ==========================
def fetch_tweets(client, query, max_pages=3):
    """
    Fetch tweets safely with pagination.
    """
    all_tweets = []

    paginator = Paginator(
        client.search_recent_tweets,
        query=f"{query} -is:retweet lang:en",
        tweet_fields=["created_at", "public_metrics"],
        max_results=100
    )

    for page_number, page in enumerate(paginator, start=1):
        print(f"[Twitter] Fetching page {page_number}...")

        if not page.data:
            break

        for tweet in page.data:
            metrics = tweet.public_metrics or {}
            all_tweets.append({
                "Source": "Twitter",
                "Content": tweet.text,
                "Subreddit": None,        # Placeholder to match Reddit format
                "Author": None,           # Twitter doesn't return usernames in this example
                "Score": metrics.get("like_count", 0),
                "Num_Comments": metrics.get("retweet_count", 0),
                "Created_At": tweet.created_at
            })

        if page_number >= max_pages:
            print("[Twitter] Reached safe page limit. Stopping pagination.")
            break

    return pd.DataFrame(all_tweets)


# ==========================
# Main Twitter Search Function
# ==========================
def search_twitter(query, max_pages=3):
    client = authenticate_twitter()
    return fetch_tweets(client, query, max_pages=max_pages)

import os
import re
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from mastodon import Mastodon
from bs4 import BeautifulSoup

load_dotenv()

def clean_html(html_content):
    """Strips HTML tags from Mastodon post content."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

# ==========================
# Mastodon Authentication
# ==========================
def authenticate_mastodon():
    access_token = os.getenv("MASTODON_ACCESS_TOKEN")
    api_base_url = os.getenv("MASTODON_INSTANCE_URL")
    
    if not access_token or not api_base_url:
        print("[Mastodon] Credentials not found. Skipping.")
        return None

    try:
        mastodon = Mastodon(access_token=access_token, api_base_url=api_base_url)
        print(f"[Mastodon] Authentication successful for {api_base_url}")
        return mastodon
    except Exception as e:
        print(f"[Mastodon] Authentication failed: {e}")
        return None

# ==========================
# Fetch Mastodon Data
# ==========================
def fetch_mastodon_data(query, num_items=100):
    """Searches the federated timeline for a hashtag."""
    mastodon = authenticate_mastodon()
    if not mastodon:
        return pd.DataFrame()

    # Mastodon API is most effective at searching the first word of a query as a hashtag
    hashtag = query.split(' ')[0].strip().lower()
    print(f"[Mastodon] Searching for hashtag: '{hashtag}'")

    try:
        # limit can be up to 40
        toots = mastodon.timeline_hashtag(hashtag, limit=min(num_items, 40))
    except Exception as e:
        print(f"[Mastodon] Error fetching data: {e}")
        return pd.DataFrame()

    posts = []
    for toot in toots:
        posts.append({
            "Source": "Mastodon",
            "Content": clean_html(toot.get('content')),
            "Subreddit": None,
            "Author": toot.get('account', {}).get('acct'),
            "Score": toot.get('favourites_count'),
            "Num_Comments": toot.get('replies_count'),
            "Created_At": toot.get('created_at')
        })

    return pd.DataFrame(posts)
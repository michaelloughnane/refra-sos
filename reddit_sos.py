import praw
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

# ==========================
# Reddit API Authentication
# ==========================
def reddit_client():
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "refra-sos-app/0.1")
    )

# ==========================
# Fetch Reddit Data
# ==========================
def fetch_reddit_data(query, subreddit="all", num_items=100):
    """
    Search Reddit for posts matching a query.
    """
    print(f"[Reddit] Searching for '{query}' in r/{subreddit}...")
    reddit = reddit_client()

    posts = []
    try:
        for submission in reddit.subreddit(subreddit).search(query, limit=num_items):
            posts.append({
                "Source": "Reddit",
                "Content": submission.title,
                "Subreddit": submission.subreddit.display_name,
                "Author": str(submission.author) if submission.author else None,
                "Score": submission.score,
                "Num_Comments": submission.num_comments,
                "Created_At": datetime.fromtimestamp(submission.created_utc)
            })
    except Exception as e:
        print(f"[Reddit] Error fetching data: {e}")
        return pd.DataFrame()

    print(f"[Reddit] Retrieved {len(posts)} posts.")
    return pd.DataFrame(posts)

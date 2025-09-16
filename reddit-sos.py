import os
import praw
import pandas as pd
from datetime import datetime
import time

# -------------------------------
# Reddit Authentication
# -------------------------------
def authenticate_reddit():
    """
    Authenticates with the Reddit API using PRAW.
    Requires environment variables:
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
    """
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "FloodRiskApp/0.1")

    if not client_id or not client_secret:
        raise ValueError("Missing Reddit API credentials. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET as environment variables.")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    return reddit

# -------------------------------
# Reddit Search Function
# -------------------------------
def search_reddit(reddit, query, subreddit="all", num_items=100):
    """
    Searches Reddit for submissions matching the query.

    Args:
        reddit (praw.Reddit): Authenticated PRAW Reddit instance.
        query (str): Search query or keywords.
        subreddit (str): Subreddit name (use "all" for entire Reddit).
        num_items (int): Max number of posts to retrieve.

    Returns:
        pd.DataFrame: DataFrame with relevant fields.
    """
    posts = []
    for submission in reddit.subreddit(subreddit).search(query, limit=num_items):
        content = submission.title
        if submission.selftext:
            content += " " + submission.selftext

        posts.append([
            content,
            submission.subreddit.display_name,
            str(submission.author) if submission.author else None,
            submission.score,
            submission.num_comments,
            datetime.fromtimestamp(submission.created_utc)
        ])

    df = pd.DataFrame(posts, columns=[
        "Content", "Subreddit", "Author", "Score", "Num_Comments", "Created_At"
    ])
    return df

# -------------------------------
# Main Runner: Hourly Data Pull
# -------------------------------
def run_hourly_search(query, subreddit="all", interval=3600, num_items=200):
    reddit = authenticate_reddit()
    print("Reddit authentication successful. Starting hourly search...")

    while True:
        print(f"\n[{datetime.now()}] Running search for query: '{query}'")
        reddit_df = search_reddit(reddit, query, subreddit=subreddit, num_items=num_items)

        # Save to CSV (timestamped)
        filename = f"reddit_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        reddit_df.to_csv(filename, index=False)
        print(f"Retrieved {len(reddit_df)} posts and saved to {filename}")

        print(f"Sleeping for {interval} seconds...")
        time.sleep(interval)

# -------------------------------
# Example Usage
# -------------------------------
if __name__ == "__main__":
    # Example flood-related keywords
    FLOOD_QUERY = "flood OR flooding OR inundation OR heavy rainfall"

    # Run search hourly across all subreddits
    run_hourly_search(FLOOD_QUERY, subreddit="all", interval=3600, num_items=100)

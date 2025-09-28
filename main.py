import threading
import time
import os
import pandas as pd
from datetime import datetime

import twitter_sos
import reddit_sos
import usgs_sos

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================
# Twitter Thread
# ==========================
def twitter_runner(query, interval=3600, max_pages=3):
    print("Starting Twitter data collection thread...")
    while True:
        twitter_df = twitter_sos.search_twitter(query, max_pages=max_pages)
        save_combined_data(twitter_df, "Twitter")
        print("[Twitter] Sleeping until next cycle...")
        time.sleep(interval)


# ==========================
# Reddit Thread
# ==========================
def reddit_runner(query, subreddit="all", interval=3600, num_items=100):
    print("Starting Reddit data collection thread...")
    while True:
        reddit_df = reddit_sos.fetch_reddit_data(query, subreddit=subreddit, num_items=num_items)
        save_combined_data(reddit_df, "Reddit")
        print("[Reddit] Sleeping until next cycle...")
        time.sleep(interval)


# ==========================
# USGS Thread
# ==========================
def usgs_runner(interval=3600):
    print("Starting USGS data collection thread...")
    while True:
        usgs_df = usgs_sos.fetch_usgs_data()
        save_combined_data(usgs_df, "USGS")
        print("[USGS] Sleeping until next cycle...")
        time.sleep(interval)


# ==========================
# Save Combined Data
# ==========================
def save_combined_data(df, source_name):
    if df.empty:
        print(f"[{source_name}] No new data to save.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"{source_name.lower()}_{timestamp}.csv")

    df.to_csv(filename, index=False)
    print(f"[{source_name}] Saved {len(df)} records to {filename}")


# ==========================
# Main Runner
# ==========================
def run_all_sources():
    QUERY = "earthquake OR flood OR flooding OR heavy rainfall"

    #twitter_thread = threading.Thread(target=twitter_runner, args=(QUERY,))
    reddit_thread = threading.Thread(target=reddit_runner, args=(QUERY,))
    usgs_thread = threading.Thread(target=usgs_runner)

    # Start all threads
    #twitter_thread.start()
    reddit_thread.start()
    usgs_thread.start()

    # Keep main thread alive
    #twitter_thread.join()
    reddit_thread.join()
    usgs_thread.join()


if __name__ == "__main__":
    print("Starting combined data collection for Reddit + Twitter + USGS...")
    run_all_sources()

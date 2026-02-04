import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from newsapi import NewsApiClient

load_dotenv()

# ==========================
# NewsAPI Authentication & Fetch
# ==========================
def fetch_news_data(query, num_items=100):
    """
    Fetches news articles from NewsAPI based on a query.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        print("[NewsAPI] NEWS_API_KEY not found. Skipping.")
        return pd.DataFrame()

    print(f"[NewsAPI] Searching for articles with query: '{query}'")
    newsapi = NewsApiClient(api_key=api_key)

    try:
        # The API limits page_size for developers, typically to 100
        all_articles = newsapi.get_everything(
            q=query,
            language='en',
            sort_by='relevancy',
            page_size=min(num_items, 100) # Respect API limits
        )
    except Exception as e:
        print(f"[NewsAPI] Error fetching data: {e}")
        return pd.DataFrame()

    articles = []
    for article in all_articles.get('articles', []):
        articles.append({
            "Source": "NewsAPI",
            "Content": f"{article.get('title', '')} - {article.get('description', '')}",
            "Subreddit": None,  # Standardized column
            "Author": article.get('source', {}).get('name'),
            "Score": None,  # Not applicable
            "Num_Comments": None, # Not applicable
            "Created_At": pd.to_datetime(article.get('publishedAt'))
        })

    return pd.DataFrame(articles)
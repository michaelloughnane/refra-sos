import os
import re
import pandas as pd
import tweepy
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import pycountry
import matplotlib.pyplot as plt
import seaborn as sns

# Download necessary NLTK data
try:
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords")
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")
try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")


def authenticate_twitter(consumer_key, consumer_secret, access_token, access_token_secret):
    """
    Authenticates with the Twitter API using Tweepy.

    Args:
        consumer_key (str): Your Twitter app's consumer key.
        consumer_secret (str): Your Twitter app's consumer secret.
        access_token (str): Your Twitter app's access token.
        access_token_secret (str): Your Twitter app's access token secret.

    Returns:
        tweepy.API: An authenticated Tweepy API object.
    """
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    return api


def search_tweets(api, query, lang="en", since_date="2019-07-06", num_items=1000):
    """
    Searches for tweets using the provided Tweepy API object.

    Args:
        api (tweepy.API): An authenticated Tweepy API object.
        query (str): The search query.
        lang (str, optional): The language of the tweets. Defaults to "en".
        since_date (str, optional): The start date for the search. Defaults to "2019-07-06".
        num_items (int, optional): The number of tweets to retrieve. Defaults to 1000.

    Returns:
        pd.DataFrame: A DataFrame containing the retrieved tweets.
    """
    tweets_data = []
    tweets = tweepy.Cursor(
        api.search,
        q=f"{query} -filter:retweets",
        lang=lang,
        since=since_date,
        tweet_mode="extended",
    ).items(num_items)

    for tweet in tweets:
        tweets_data.append(
            [
                tweet.full_text,
                tweet.user.location,
                tweet.user.screen_name,
                tweet.retweet_count,
                tweet.favorite_count,
                tweet.created_at,
            ]
        )

    df = pd.DataFrame(
        tweets_data,
        columns=[
            "Content",
            "Location",
            "Username",
            "Retweet-Count",
            "Favorites",
            "Created at",
        ],
    )
    return df


def preprocess_text(text):
    """
    Cleans and preprocesses a single string of text.

    Args:
        text (str): The text to process.

    Returns:
        list: A list of processed tokens.
    """
    text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\@\w+|\#", "", text)
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()
    tokens = [
        lemmatizer.lemmatize(token, pos="a")
        for token in tokens
        if token.lower() not in stop_words and token.isalpha() and len(token) > 2
    ]
    return tokens


def get_country_code(location):
    """
    Attempts to find a country code from a location string.

    Args:
        location (str): The location string.

    Returns:
        str: The alpha-2 country code or "unknown".
    """
    if not isinstance(location, str):
        return "unknown"
    try:
        country = pycountry.countries.search_fuzzy(location)
        if country:
            return country[0].alpha_2
    except LookupError:
        pass
    return "unknown"


def analyze_tweet_data(df):
    """
    Performs basic analysis on the tweet DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame of tweets.
    """
    print("## Dataframe Info")
    df.info()
    print("\n## Dataframe Description")
    print(df.describe())

    # Time-based analysis
    df["Created at"] = pd.to_datetime(df["Created at"])
    print(f"\n## Oldest Tweet: {df['Created at'].min()}")
    print(f"## Newest Tweet: {df['Created at'].max()}")

    # Location analysis
    df["Country"] = df["Location"].apply(get_country_code)
    print("\n## Tweet Counts by Country (Top 10)")
    print(df["Country"].value_counts().head(10))

    # Popularity analysis
    print("\n## Most Popular Tweets (by Favorites and Retweets)")
    popular_tweets = df.sort_values(
        by=["Favorites", "Retweet-Count"], ascending=False
    ).head(10)
    print(popular_tweets[["Content", "Retweet-Count", "Favorites"]])


def visualize_tweet_data(df):
    """
    Creates visualizations for the tweet data.

    Args:
        df (pd.DataFrame): The DataFrame of tweets.
    """
    plt.figure(figsize=(12, 6))
    sns.histplot(df["Created at"].dt.hour, bins=24, kde=True)
    plt.title("Hourly Distribution of Tweets")
    plt.xlabel("Hour of the Day")
    plt.ylabel("Number of Tweets")
    plt.show()

    top_countries = df[df["Country"] != "unknown"]["Country"].value_counts().head(10)
    if not top_countries.empty:
        country_names = [
            pycountry.countries.get(alpha_2=code).name
            for code in top_countries.index
        ]
        plt.figure(figsize=(12, 6))
        sns.barplot(x=top_countries.values, y=country_names)
        plt.title("Top 10 Countries by Tweet Count")
        plt.xlabel("Tweet Count")
        plt.ylabel("Country")
        plt.show()


if __name__ == "__main__":
    # It is highly recommended to use environment variables for your keys and tokens
    CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY", "YOUR_KEY_HERE")
    CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET", "YOUR_KEY_HERE")
    ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "YOUR_KEY_HERE")
    ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "YOUR_KEY_HERE")

    if "YOUR_KEY_HERE" in [
        CONSUMER_KEY,
        CONSUMER_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET,
    ]:
        print("Warning: Twitter API credentials are not set.")
        # You can add a sys.exit() here if you want the script to stop
        # if credentials are not provided.

    twitter_api = authenticate_twitter(
        CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
    )

    SEARCH_QUERY = "earthquake"
    tweets_df = search_tweets(twitter_api, SEARCH_QUERY)

    # Preprocess the 'Content' column
    tweets_df["Processed_Content"] = tweets_df["Content"].apply(preprocess_text)

    analyze_tweet_data(tweets_df)
    visualize_tweet_data(tweets_df)
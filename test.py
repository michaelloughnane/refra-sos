def test_preprocess_text_removes_urls_and_stopwords():
    txt = "Check this http://example.com #awesome"
    tokens = preprocess_text(txt)
    assert "check" in tokens and "awesome" in tokens  # URL removed, hashtag gone
def test_preprocess_text_lowercases_and_lemmatizes():
    txt = "Running runners run"
    tokens = preprocess_text(txt)
    # All forms of "run" should appear lemmatized to their base (e.g., "run")
    assert all(token.lower() == "run" for token in tokens)
def test_get_country_code_known_country():
    assert get_country_code("United States") == "US"
    assert get_country_code("Germany") == "DE"

def test_get_country_code_unknown_or_invalid():
    assert get_country_code("Atlantis") == "unknown"    # Fuzzy search fails
    assert get_country_code(12345) == "unknown"        # Non-string input
def test_authenticate_twitter_returns_api(monkeypatch):
    class DummyAuth: 
        def set_access_token(self, a, b): pass
    class DummyAPI: pass
    # Patch OAuthHandler to return dummy auth
    monkeypatch.setattr(tweepy, "OAuthHandler", lambda k,s: DummyAuth())
    # Patch API to return DummyAPI instance
    monkeypatch.setattr(tweepy, "API", lambda auth, wait_on_rate_limit: DummyAPI())
    api = authenticate_twitter("key","secret","token","tokensecret")
    assert isinstance(api, DummyAPI)
def test_search_tweets_with_mocked_cursor(monkeypatch):
    # Create a fake tweet object
    class FakeUser: 
        def __init__(self, loc): self.location = loc
    class FakeTweet:
        def __init__(self, text, loc):
            self.full_text = text
            self.user = FakeUser(loc)
            self.retweet_count = 1
            self.favorite_count = 2
            self.created_at = pd.Timestamp("2020-01-01")
    fake_tweets = [FakeTweet("Hello", "USA"), FakeTweet("World", "Canada")]

    # Patch tweepy.Cursor to ignore real API and return our fake tweets
    class DummyCursor:
        def __init__(self, *args, **kwargs): pass
        def items(self, num): return fake_tweets
    monkeypatch.setattr(tweepy, "Cursor", lambda *args, **kwargs: DummyCursor())

    dummy_api = object()  # API argument isn’t used since we patched Cursor
    df = search_tweets(dummy_api, "query", num_items=2)
    # Verify DataFrame content
    assert list(df["Content"]) == ["Hello", "World"]
    assert list(df["Location"]) == ["USA", "Canada"]
def test_analyze_tweet_data_output(capsys):
    df = pd.DataFrame({
        "Content": ["A","B"],
        "Location": ["X","Y"],
        "Username": ["u1","u2"],
        "Retweet-Count": [1, 2],
        "Favorites": [0, 1],
        "Created at": [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-02")]
    })
    analyze_tweet_data(df)
    captured = capsys.readouterr()
    assert "Dataframe Info" in captured.out
    assert "Oldest Tweet" in captured.out
    assert "Newest Tweet" in captured.out
def test_visualize_tweet_data_does_not_error(monkeypatch):
    df = pd.DataFrame({
        "Created at": [pd.Timestamp("2020-01-01 12:00"), pd.Timestamp("2020-01-01 13:00")],
        "Country": ["US", "CA"]
    })
    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)
    visualize_tweet_data(df)
    # If no exception is raised, we assume plotting was attempted correctly.
from pandas.testing import assert_frame_equal

def test_search_tweets_dataframe_content(monkeypatch):
    # ... (set up fake tweets as above) ...
    df = search_tweets(dummy_api, "q", num_items=1)
    expected = pd.DataFrame([{
        "Content": "Hello",
        "Location": "USA",
        "Username": "u1",
        "Retweet-Count": 1,
        "Favorites": 0,
        "Created at": pd.Timestamp("2020-01-01")
    }])
    assert_frame_equal(df.reset_index(drop=True), expected.reset_index(drop=True))

import os 
import requests
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

def create_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "v2RecentSearchPython"
    }
def test_connectivity():
    url = "https://api.twitter.com/2/tweets/search/recent"
    query_params = {
        "query": "python",
        "max_results": 15
    }
    headers = create_headers(BEARER_TOKEN)
    response = requests.get(url,headers=headers,params=query_params)
    print("Rate limit remaining:", response.headers.get("x-rate-limit-remaining"))
    print("Rate limit reset at:", response.headers.get("x-rate-limit-reset"))


    if response.status_code ==200:
        print("Successful Connection")
        print("Tweets:")
        for tweet in response.json().get("data",[]):
            print("-",tweet["text"])
    else:
        print("Error:",response.status_code,response.text)
    
if __name__ == "__main__":
    test_connectivity()
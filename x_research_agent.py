import os
import json
import datetime
from dotenv import load_dotenv
from openai import OpenAI
import tweepy

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
OUTPUT_FILE = "x_research_output.json"

# Initialize clients
openai_client = OpenAI()
x_client = tweepy.Client(bearer_token=X_BEARER_TOKEN)

def search_tweets(query, max_results=100):
    """
    Search for tweets using X API v2
    For now, return mock data since we don't have X API credentials
    """
    # Mock data for development
    sample_tweets = [
        {
            "id": "1234567890",
            "text": "Bitcoin is the future of money. The separation of money and state is inevitable.",
            "author": "michael_saylor",
            "metrics": {
                "likes": 1500,
                "retweets": 500,
                "replies": 200
            },
            "created_at": "2025-04-01T10:00:00Z"
        },
        {
            "id": "1234567891",
            "text": "Just bought more #Bitcoin at 100k. Still early.",
            "author": "bitcoiner",
            "metrics": {
                "likes": 800,
                "retweets": 300,
                "replies": 100
            },
            "created_at": "2025-04-01T11:00:00Z"
        }
    ]
    return sample_tweets

def analyze_user(username):
    """
    Analyze a Twitter user's Bitcoin-related content
    For now, return mock data
    """
    return {
        "username": username,
        "followers": 50000,
        "total_tweets": 1000,
        "bitcoin_tweets": 500,
        "engagement_rate": 0.05,
        "common_topics": ["Bitcoin", "Lightning Network", "Sovereignty"]
    }

def analyze_trends():
    """
    Analyze current Bitcoin trends on X
    For now, return mock data
    """
    return {
        "trending_topics": [
            {"topic": "#Bitcoin", "tweet_count": 50000},
            {"topic": "#BTC", "tweet_count": 30000},
            {"topic": "Satoshi", "tweet_count": 10000}
        ],
        "sentiment": {
            "positive": 0.6,
            "neutral": 0.3,
            "negative": 0.1
        },
        "peak_activity_hours": ["09:00", "15:00", "20:00"]
    }

def analyze_x_data(query=None, usernames=None):
    """Main function to analyze X data"""
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "query_results": [],
        "user_analyses": [],
        "trends": None,
        "insights": None
    }
    
    # Search tweets if query provided
    if query:
        tweets = search_tweets(query)
        data["query_results"] = tweets
    
    # Analyze users if usernames provided
    if usernames:
        for username in usernames:
            user_analysis = analyze_user(username)
            data["user_analyses"].append(user_analysis)
    
    # Get trend analysis
    data["trends"] = analyze_trends()
    
    # Generate insights using GPT-4
    prompt = f"""
    Analyze this Bitcoin-related X (Twitter) data and provide:
    1. Key engagement patterns
    2. Popular narratives
    3. Influential voices
    4. Content opportunities
    5. Best posting times
    6. Hashtag strategy

    Data:
    {json.dumps(data, indent=2)}
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    
    data["insights"] = response.choices[0].message.content.strip()
    
    # Save results
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved X research insights to {OUTPUT_FILE}")
    return data

def run_x_research(query=None, usernames=None):
    """Run the X research agent with the given parameters"""
    try:
        return analyze_x_data(query, usernames)
    except Exception as e:
        print(f"Error running X research: {str(e)}")
        return None

if __name__ == "__main__":
    # Example usage
    query = "bitcoin OR #btc"
    usernames = ["michael_saylor", "bitcoinmagazine"]
    run_x_research(query, usernames)

import tweepy
from dotenv import load_dotenv
import os
import json
import datetime

# Load environment variables
load_dotenv(dotenv_path='/Users/matthew/CascadeProjects/Xagents/.env')
bearer_token = os.getenv("BEARER_TOKEN")

# Constants
TWEETS_OUTPUT = "tweets.json"

# Tweepy client
twitter_client = tweepy.Client(bearer_token=bearer_token)

def download_tweets(username, max_tweets=10):
    try:
        user = twitter_client.get_user(username=username)
        tweets = twitter_client.get_users_tweets(
            id=user.data.id,
            max_results=min(max_tweets, 100),
            tweet_fields=["created_at", "text"]
        )
        
        if not tweets.data:
            return []
            
        tweet_list = []
        for tweet in tweets.data:
            tweet_data = {
                "text": tweet.text,
                "id": tweet.id,
                "collected_at": datetime.datetime.now().isoformat()
            }
            tweet_list.append(tweet_data)
        return tweet_list
    except Exception as e:
        print(f"Error fetching tweets from @{username}: {str(e)}")
        return []

def save_tweets(usernames, filename=TWEETS_OUTPUT):
    # Load existing tweets if available
    try:
        with open(filename, "r") as f:
            all_tweets = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_tweets = {}

    # Initialize any new usernames
    for user in usernames:
        if user not in all_tweets:
            all_tweets[user] = []

    # Download and append new tweets
    new_tweet_count = 0
    for user in usernames:
        new_tweets = download_tweets(user)
        if new_tweets:
            # Only add tweets that aren't already in the collection
            existing_ids = {t.get('id') for t in all_tweets[user]}
            for tweet in new_tweets:
                if tweet.get('id') not in existing_ids:
                    all_tweets[user].append(tweet)
                    new_tweet_count += 1

    # Save updated tweets
    with open(filename, "w") as f:
        json.dump(all_tweets, f, indent=4)
    print(f"Added {new_tweet_count} new tweets to {filename}")
    return all_tweets

if __name__ == "__main__":
    target_users = ["rajatsonifnance", "Bitcoin_Teddy", "TheCryptoLark", 
                    "BitwiseInvest", "IIICapital", "DocumentingBTC"]
    save_tweets(target_users)

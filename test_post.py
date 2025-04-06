import tweepy
from datetime import datetime
import os
from dotenv import load_dotenv

# Force reload environment variables
os.environ.clear()
load_dotenv(override=True, verbose=True)

def test_twitter_api():
    try:
        # Get credentials from environment variables
        api_key = os.getenv('X_API_KEY')
        api_secret = os.getenv('X_API_SECRET')
        access_token = os.getenv('X_ACCESS_TOKEN')
        access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')
        
        print("\nDebug: Using credentials:")
        print(f"API Key: {api_key}")
        print(f"API Secret: {api_secret[:8]}...")
        print(f"Access Token: {access_token[:8]}...")
        
        # Initialize Twitter API v2 client
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )
        
        print("\nTesting authentication...")
        me = client.get_me()
        print(f"✓ Authenticated as @{me.data.username}")
        
        # Test posting
        timestamp = datetime.now().strftime("%H:%M:%S")
        test_tweet = f"Test tweet at {timestamp} - will be deleted immediately"
        print(f"\nPosting test tweet: {test_tweet}")
        
        # Post the tweet
        response = client.create_tweet(text=test_tweet)
        tweet_id = response.data['id']
        print(f"✓ Tweet posted successfully (ID: {tweet_id})")
        
        # Delete the test tweet
        print("\nDeleting test tweet...")
        client.delete_tweet(tweet_id)
        print("✓ Tweet deleted successfully")
        
        return True
            
    except tweepy.errors.Unauthorized as e:
        print(f"\nAuthorization Error: {str(e)}")
        print("\nDebug Information:")
        print(f"API Key: {api_key[:8]}...")
        print(f"Access Token: {access_token[:8]}...")
        return False
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Twitter API connection...")
    success = test_twitter_api()
    print(f"\nTest {'succeeded' if success else 'failed'}")

import json
import tweepy
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
import sys

def check_env_vars():
    """Verify all required environment variables are set."""
    required_vars = ['X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
        return False
    return True

def load_schedule():
    """Load and validate the schedule file."""
    try:
        if not os.path.exists('scheduled_posts.json'):
            print("Error: scheduled_posts.json not found")
            return None
            
        with open('scheduled_posts.json', 'r') as f:
            data = json.load(f)
            
        if not isinstance(data, dict) or 'schedule' not in data:
            print("Error: Invalid format in scheduled_posts.json")
            return None
            
        # Initialize post status if not present
        for post in data['schedule']:
            if 'status' not in post:
                post['status'] = 'pending'
            if 'attempts' not in post:
                post['attempts'] = 0
                
        print(f"Schedule loaded successfully. Found {len(data['schedule'])} posts.")
        return data
    except json.JSONDecodeError:
        print("Error: Invalid JSON in scheduled_posts.json")
        return None
    except Exception as e:
        print(f"Error reading schedule: {str(e)}")
        return None

def get_twitter_client():
    """Initialize the Twitter API client."""
    try:
        client = tweepy.Client(
            consumer_key=os.getenv('X_API_KEY'),
            consumer_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
            wait_on_rate_limit=True
        )
        # Test the credentials with a simple call
        client.get_me()
        print("Twitter client initialized and authenticated successfully")
        return client
    except Exception as e:
        print(f"Error initializing Twitter client: {str(e)}")
        return None

def find_due_post(data, current_time):
    """Find the earliest pending post that is due."""
    due_post = None
    earliest_time = None
    est = pytz.timezone('America/New_York')
    
    for post in data['schedule']:
        try:
            # Skip posts that are already handled
            if post['status'] in ['posted', 'error_duplicate']:
                continue
                
            scheduled_time = datetime.strptime(post['time'], '%Y-%m-%d %H:%M:%S')
            scheduled_time = est.localize(scheduled_time)
            
            if current_time >= scheduled_time and (earliest_time is None or scheduled_time < earliest_time):
                due_post = post
                earliest_time = scheduled_time
        except (ValueError, KeyError) as e:
            print(f"Warning: Invalid post format: {str(e)}")
            continue
    
    return due_post, earliest_time

def save_schedule(data):
    """Save the schedule back to file."""
    try:
        with open('scheduled_posts.json', 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving schedule: {str(e)}")
        return False

def update_post_status(data, post, status, tweet_id=None):
    """Update post status and save to file."""
    post['status'] = status
    post['attempts'] += 1
    post['last_attempt'] = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
    if tweet_id:
        post['tweet_id'] = tweet_id
    return save_schedule(data)

def post_due_tweets():
    """Main function to post due tweets."""
    print("\n=== Starting tweet posting process ===")
    
    # Load environment variables from both .env and system
    load_dotenv()
    
    # Check environment variables
    if not check_env_vars():
        sys.exit(1)
    
    # Initialize Twitter client
    client = get_twitter_client()
    if client is None:
        sys.exit(1)
    
    # Load schedule
    data = load_schedule()
    if data is None:
        sys.exit(1)
    
    # Get current time in EST
    est = pytz.timezone('America/New_York')
    current_time = datetime.now(est)
    print(f"Current time (EST): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find due post
    due_post, earliest_time = find_due_post(data, current_time)
    
    # Post tweet if one is due
    if due_post:
        try:
            print(f"Attempting to post tweet scheduled for {earliest_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Tweet content: {due_post['content']}")
            
            response = client.create_tweet(text=due_post['content'])
            tweet_id = response.data['id']
            print(f"Successfully posted tweet at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Tweet ID: {tweet_id}")
            
            # Update post status
            if update_post_status(data, due_post, 'posted', tweet_id):
                print("Updated post status to 'posted'")
            else:
                print("Warning: Failed to update post status")
            
        except tweepy.errors.Forbidden as e:
            error_message = str(e).lower()
            if "duplicate" in error_message:
                print("Duplicate tweet detected, marking as duplicate and skipping...")
                update_post_status(data, due_post, 'error_duplicate')
            else:
                print(f"Permission error posting tweet: {str(e)}")
                update_post_status(data, due_post, 'error_permission')
        except tweepy.TooManyRequests as e:
            print(f"Rate limit exceeded: {str(e)}")
            update_post_status(data, due_post, 'error_rate_limit')
            sys.exit(1)
        except Exception as e:
            print(f"Error posting tweet: {str(e)}")
            update_post_status(data, due_post, 'error_unknown')
    else:
        print("No pending posts are due at this time")

if __name__ == "__main__":
    try:
        post_due_tweets()
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

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
    print("✓ All required environment variables are set")
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
            
        print(f"✓ Schedule loaded successfully. Found {len(data['schedule'])} posts.")
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
        me = client.get_me()
        print(f"✓ Twitter client initialized and authenticated successfully as @{me.data.username}")
        return client
    except Exception as e:
        print(f"Error initializing Twitter client: {str(e)}")
        return None

def delete_all_previous_tweets(api):
    """Delete all tweets from the authenticated user's timeline."""
    try:
        user = api.verify_credentials()
        for status in tweepy.Cursor(api.user_timeline, user_id=user.id, tweet_mode="extended").items():
            try:
                api.destroy_status(status.id)
                print(f"Deleted tweet ID: {status.id}")
            except Exception as e:
                print(f"Failed to delete tweet ID {status.id}: {e}")
        print("All previous tweets deleted.")
    except Exception as e:
        print(f"Error deleting previous tweets: {e}")

def find_due_post(data, current_time):
    """Find the earliest pending post that is due."""
    due_post = None
    earliest_time = None
    est = pytz.timezone('America/New_York')
    
    print(f"\nCurrent time (UTC): {current_time}")
    print(f"Current time (EST): {current_time.astimezone(est)}\n")
    
    for post in data['schedule']:
        try:
            # Skip posts that are already handled or errored
            if post['status'] != 'pending' or post.get('attempts', 0) >= 3:
                continue
                
            scheduled_time = datetime.strptime(post['time'], '%Y-%m-%d %H:%M:%S')
            scheduled_time = est.localize(scheduled_time)
            
            # Skip posts that are more than 24 hours old to avoid duplicate issues
            if (current_time - scheduled_time).total_seconds() > 86400:  # 24 hours in seconds
                print(f"Skipping old post scheduled for {scheduled_time} (more than 24h old)")
                update_post_status(data, post, 'error_expired')
                continue
            
            if current_time >= scheduled_time and (earliest_time is None or scheduled_time < earliest_time):
                due_post = post
                earliest_time = scheduled_time
                
            # Debug output for each post
            is_due = current_time >= scheduled_time
            print(f"Post: '{post['content'][:50]}...'")
            print(f"  Scheduled: {scheduled_time}")
            print(f"  Status: {post['status']}")
            print(f"  Due: {'Yes' if is_due else 'No'}\n")
                
        except (ValueError, KeyError) as e:
            print(f"Warning: Invalid post format: {str(e)}")
            continue
    
    if due_post:
        print(f"✓ Found due post scheduled for {earliest_time}")
        print(f"  Content: {due_post['content']}")
    else:
        print("No pending posts are due")
        
    return due_post, earliest_time

def save_schedule(data):
    """Save the schedule back to file."""
    try:
        with open('scheduled_posts.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("✓ Successfully saved schedule to file")
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
    saved = save_schedule(data)
    print(f"Updated post status to '{status}' and {'saved' if saved else 'failed to save'} to file")
    return saved

def post_due_tweets():
    """Main function to post due tweets."""
    print("\n=== Starting tweet posting process ===")
    print(f"Script running from: {os.getcwd()}")
    
    # Load environment variables from both .env and system
    load_dotenv()
    
    # Debug environment variables (without exposing secrets)
    for var in ['X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET']:
        print(f"{var} is {'set' if os.getenv(var) else 'NOT SET'}")
    
    # Check environment variables
    if not check_env_vars():
        print("Failed environment variable check")
        sys.exit(1)
    
    # Authenticate Tweepy API
    auth = tweepy.OAuth1UserHandler(
        os.getenv('X_API_KEY'),
        os.getenv('X_API_SECRET'),
        os.getenv('X_ACCESS_TOKEN'),
        os.getenv('X_ACCESS_TOKEN_SECRET')
    )
    api = tweepy.API(auth)
    
    # Delete all previous tweets before posting new ones
    delete_all_previous_tweets(api)
    
    # Initialize Twitter client
    try:
        client = get_twitter_client()
        if client is None:
            print("Failed to initialize Twitter client")
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error initializing Twitter client: {str(e)}")
        sys.exit(1)
    
    # Load schedule
    try:
        data = load_schedule()
        if data is None:
            print("Failed to load schedule")
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error loading schedule: {str(e)}")
        sys.exit(1)
    
    # Get current time in EST
    est = pytz.timezone('America/New_York')
    current_time = datetime.now(est)
    print(f"Current time (EST): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Find due post
    try:
        due_post, earliest_time = find_due_post(data, current_time)
    except Exception as e:
        print(f"Unexpected error finding due post: {str(e)}")
        sys.exit(1)
    
    # Post tweet if one is due
    if due_post:
        try:
            print(f"Attempting to post tweet scheduled for {earliest_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"Tweet content: {due_post['content']}")
            
            response = client.create_tweet(text=due_post['content'])
            tweet_id = response.data['id']
            print(f"Successfully posted tweet at {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"Tweet ID: {tweet_id}")
            
            # Update post status
            if update_post_status(data, due_post, 'posted', tweet_id):
                print("Updated post status to 'posted'")
            else:
                print("Warning: Failed to update post status")
            
        except tweepy.errors.Forbidden as e:
            error_message = str(e).lower()
            print(f"Full error message: {error_message}")
            if "duplicate" in error_message:
                print("Duplicate tweet detected, marking as duplicate and skipping...")
                update_post_status(data, due_post, 'error_duplicate')
            else:
                print(f"Permission error posting tweet: {str(e)}")
                update_post_status(data, due_post, 'error_permission')
                sys.exit(1)
        except tweepy.TooManyRequests as e:
            print(f"Rate limit exceeded: {str(e)}")
            update_post_status(data, due_post, 'error_rate_limit')
            sys.exit(1)
        except Exception as e:
            print(f"Error posting tweet: {str(e)}")
            update_post_status(data, due_post, 'error_unknown')
            sys.exit(1)
    else:
        print("No pending posts are due at this time")

if __name__ == "__main__":
    try:
        post_due_tweets()
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

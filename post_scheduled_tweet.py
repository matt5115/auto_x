import json
import tweepy
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
import sys

def post_due_tweets():
    try:
        # Load environment variables
        load_dotenv()
        
        # Verify environment variables
        required_vars = ['X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
            sys.exit(1)
        
        # Initialize Twitter API v2 client
        client = tweepy.Client(
            consumer_key=os.getenv('X_API_KEY'),
            consumer_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
            wait_on_rate_limit=True
        )
        
        # Get current time in EST
        est = pytz.timezone('America/New_York')
        current_time = datetime.now(est)
        print(f"Current time (EST): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Verify scheduled_posts.json exists
        if not os.path.exists('scheduled_posts.json'):
            print("Error: scheduled_posts.json not found")
            sys.exit(1)
            
        # Load schedule
        try:
            with open('scheduled_posts.json', 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in scheduled_posts.json")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading scheduled_posts.json: {str(e)}")
            sys.exit(1)
            
        if not isinstance(data, dict) or 'schedule' not in data:
            print("Error: Invalid format in scheduled_posts.json")
            sys.exit(1)
            
        # Find the earliest scheduled post that's due
        due_post = None
        earliest_time = None
        
        for post in data['schedule']:
            try:
                scheduled_time = datetime.strptime(post['time'], '%Y-%m-%d %H:%M:%S')
                scheduled_time = est.localize(scheduled_time)
                
                # If post is due and either it's the first due post we've found
                # or it's earlier than our current earliest
                if current_time >= scheduled_time and (earliest_time is None or scheduled_time < earliest_time):
                    due_post = post
                    earliest_time = scheduled_time
            except (ValueError, KeyError) as e:
                print(f"Warning: Invalid post format in schedule: {str(e)}")
                continue
        
        # If we found a due post, post it
        if due_post:
            try:
                print(f"Attempting to post tweet scheduled for {earliest_time.strftime('%Y-%m-%d %H:%M:%S')}...")
                response = client.create_tweet(text=due_post['content'])
                print(f"Successfully posted tweet at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Remove the posted tweet from schedule
                data['schedule'] = [post for post in data['schedule'] if post != due_post]
                with open('scheduled_posts.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("Removed posted tweet from schedule")
                
            except tweepy.TooManyRequests as e:
                print(f"Rate limit exceeded: {str(e)}")
                sys.exit(1)
            except Exception as e:
                print(f"Error posting tweet: {str(e)}")
                sys.exit(1)
        else:
            print("No posts are due at this time")
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    post_due_tweets()

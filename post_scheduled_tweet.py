import json
import tweepy
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
import time

def post_due_tweets():
    # Load environment variables
    load_dotenv()
    
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
    
    try:
        # Load schedule
        with open('scheduled_posts.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("No scheduled posts found")
        return
    
    # Track which posts to remove
    posts_to_remove = []
    posts_attempted = 0
    
    # Check for posts that should be posted now
    for post in data['schedule']:
        # If we've attempted 3 posts in this run, stop to avoid rate limits
        if posts_attempted >= 3:
            print("Reached post limit for this run. Remaining posts will be handled in next run.")
            break
            
        scheduled_time = datetime.strptime(post['time'], '%Y-%m-%d %H:%M:%S')
        scheduled_time = est.localize(scheduled_time)
        
        # If it's time to post (or past time), post it
        if current_time >= scheduled_time:
            try:
                print(f"Attempting to post: {post['content'][:50]}...")
                response = client.create_tweet(text=post['content'])
                print(f"Successfully posted tweet at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                posts_to_remove.append(post)
                posts_attempted += 1
                
                # Add a delay between posts to avoid rate limits
                if posts_attempted < 3:
                    print("Waiting 30 seconds before next post...")
                    time.sleep(30)
                    
            except tweepy.TooManyRequests as e:
                print(f"Rate limit exceeded. Will try again in next run.")
                break
            except Exception as e:
                print(f"Error posting tweet: {str(e)}")
    
    # Remove posted tweets from schedule
    if posts_to_remove:
        data['schedule'] = [post for post in data['schedule'] if post not in posts_to_remove]
        with open('scheduled_posts.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Removed {len(posts_to_remove)} posted tweets from schedule")
    else:
        print("No posts were due at this time")

if __name__ == "__main__":
    post_due_tweets()

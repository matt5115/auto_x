import json
import tweepy
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

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
    
    # Load schedule
    with open('scheduled_posts.json', 'r') as f:
        data = json.load(f)
    
    # Track which posts to remove
    posts_to_remove = []
    
    # Check for posts that should be posted now
    for post in data['schedule']:
        scheduled_time = datetime.strptime(post['time'], '%Y-%m-%d %H:%M:%S')
        scheduled_time = est.localize(scheduled_time)
        
        # If it's time to post (or past time), post it
        if current_time >= scheduled_time:
            try:
                response = client.create_tweet(text=post['content'])
                print(f"Posted tweet: {post['content'][:50]}...")
                posts_to_remove.append(post)
            except Exception as e:
                print(f"Error posting tweet: {str(e)}")
    
    # Remove posted tweets from schedule
    if posts_to_remove:
        data['schedule'] = [post for post in data['schedule'] if post not in posts_to_remove]
        with open('scheduled_posts.json', 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    post_due_tweets()

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
    
    try:
        # Load schedule
        with open('scheduled_posts.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("No scheduled posts found")
        return
    
    # Find the earliest scheduled post that's due
    due_post = None
    earliest_time = None
    
    for post in data['schedule']:
        scheduled_time = datetime.strptime(post['time'], '%Y-%m-%d %H:%M:%S')
        scheduled_time = est.localize(scheduled_time)
        
        # If post is due and either it's the first due post we've found
        # or it's earlier than our current earliest
        if current_time >= scheduled_time and (earliest_time is None or scheduled_time < earliest_time):
            due_post = post
            earliest_time = scheduled_time
    
    # If we found a due post, post it
    if due_post:
        try:
            print(f"Attempting to post: {due_post['content'][:50]}...")
            response = client.create_tweet(text=due_post['content'])
            print(f"Successfully posted tweet at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Remove the posted tweet from schedule
            data['schedule'] = [post for post in data['schedule'] if post != due_post]
            with open('scheduled_posts.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("Removed posted tweet from schedule")
            
        except tweepy.TooManyRequests as e:
            print(f"Rate limit exceeded. Will try again in next run.")
        except Exception as e:
            print(f"Error posting tweet: {str(e)}")
    else:
        print("No posts are due at this time")

if __name__ == "__main__":
    post_due_tweets()

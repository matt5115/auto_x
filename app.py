from flask import Flask, request, jsonify, render_template
import logging
import os
from dotenv import load_dotenv
import user_recommender
import x_research_agent
import youtube_research_agent
import editor_agent
import json
import tweepy
import pytz
import threading
import time
import sys

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")

# ... (rest of the original code remains the same)

def post_due_tweets():
    while True:
        try:
            # Load environment variables
            load_dotenv()
            
            # Get current time in EST
            est = pytz.timezone('America/New_York')
            current_time = datetime.now(est)
            print(f"\nChecking for tweets at {current_time.strftime('%Y-%m-%d %H:%M:%S')} EST")
            
            # Load schedule
            try:
                with open('scheduled_posts.json', 'r') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading schedule: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
                continue
                
            # Find the earliest scheduled post that's due
            due_post = None
            earliest_time = None
            
            for post in data.get('schedule', []):
                try:
                    scheduled_time = datetime.strptime(post['time'], '%Y-%m-%d %H:%M:%S')
                    scheduled_time = est.localize(scheduled_time)
                    
                    if current_time >= scheduled_time and (earliest_time is None or scheduled_time < earliest_time):
                        due_post = post
                        earliest_time = scheduled_time
                except Exception as e:
                    print(f"Error processing post: {str(e)}")
                    continue
            
            # If we found a due post, post it
            if due_post:
                try:
                    # Initialize Twitter client
                    client = tweepy.Client(
                        consumer_key=os.getenv('X_API_KEY'),
                        consumer_secret=os.getenv('X_API_SECRET'),
                        access_token=os.getenv('X_ACCESS_TOKEN'),
                        access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
                        wait_on_rate_limit=True
                    )
                    
                    print(f"Posting tweet scheduled for {earliest_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    response = client.create_tweet(text=due_post['content'])
                    print(f"Successfully posted tweet at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Remove the posted tweet from schedule
                    data['schedule'] = [post for post in data['schedule'] if post != due_post]
                    with open('scheduled_posts.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print("Removed posted tweet from schedule")
                    
                except Exception as e:
                    print(f"Error posting tweet: {str(e)}")
            
            # Sleep for 1 minute before next check
            time.sleep(60)
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying

@app.route('/tweet_scheduler')
def tweet_scheduler_home():
    return 'Tweet Scheduler is running'

@app.route('/tweet_scheduler/health')
def tweet_scheduler_health():
    return 'OK'

def start_scheduler():
    scheduler_thread = threading.Thread(target=post_due_tweets)
    scheduler_thread.daemon = True
    scheduler_thread.start()

if __name__ == '__main__':
    # Start the scheduler in a separate thread
    start_scheduler()
    # Run the Flask app
    app.run(debug=True, port=5009)

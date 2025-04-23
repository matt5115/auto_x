import json
from datetime import datetime, timedelta
import pytz
import random
import os

# Get the directory containing this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BITCOIN_TWEETS_FILE = os.path.join(SCRIPT_DIR, "bitcoin_tweets.json")
SCHEDULE_FILE = os.path.join(SCRIPT_DIR, "scheduled_posts.json")

# Optimal post times in EST
OPTIMAL_HOURS = [9, 13, 17]  # 9am, 1pm, 5pm

def load_bitcoin_tweets():
    with open(BITCOIN_TWEETS_FILE, "r") as f:
        return json.load(f)

def schedule_new_posts():
    # Load all 100 Bitcoin tweets
    tweets = load_bitcoin_tweets()
    # Shuffle for randomness, or keep order if desired
    random.shuffle(tweets)

    # Schedule 3 per day at optimal times
    est = pytz.timezone('America/New_York')
    now = datetime.now(est)
    schedule = []
    tweet_idx = 0
    day = now
    while tweet_idx < len(tweets):
        for hour in OPTIMAL_HOURS:
            if tweet_idx >= len(tweets):
                break
            scheduled_time = day.replace(hour=hour, minute=0, second=0, microsecond=0)
            if scheduled_time < now:
                scheduled_time += timedelta(days=1)
            schedule.append({
                "content": tweets[tweet_idx],
                "time": scheduled_time.strftime('%Y-%m-%d %H:%M:%S'),
                "status": "pending",
                "attempts": 0
            })
            tweet_idx += 1
        day += timedelta(days=1)
    # Save schedule
    with open(SCHEDULE_FILE, "w") as f:
        json.dump({"schedule": schedule}, f, indent=2)
    print(f"Scheduled {len(schedule)} Bitcoin tweets (3 per day)")

if __name__ == "__main__":
    schedule_new_posts()

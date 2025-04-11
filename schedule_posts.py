import json
import datetime
import pytz
import os

def load_raw_posts():
    """Load posts from raw_posts.json"""
    try:
        with open('raw_posts.json', 'r') as f:
            data = json.load(f)
            return data.get('raw_posts', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading raw posts: {str(e)}")
        return []

def load_scheduled_posts():
    """Load existing scheduled posts"""
    try:
        with open('scheduled_posts.json', 'r') as f:
            data = json.load(f)
            return data.get('schedule', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def schedule_new_posts():
    """Schedule new posts from raw_posts.json"""
    raw_posts = load_raw_posts()
    scheduled_posts = load_scheduled_posts()
    
    # Get content of existing scheduled posts to avoid duplicates
    existing_content = {post['content'] for post in scheduled_posts}
    
    # Get current time in EST
    est = pytz.timezone('America/New_York')
    current_time = datetime.datetime.now(est)
    
    # Schedule posts 15 minutes apart starting from now
    new_scheduled_posts = []
    post_time = current_time
    
    for post in raw_posts:
        if post['content'] not in existing_content:
            scheduled_post = {
                'content': post['content'],
                'time': post_time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'pending',
                'attempts': 0
            }
            new_scheduled_posts.append(scheduled_post)
            existing_content.add(post['content'])
            post_time += datetime.timedelta(minutes=15)
    
    # Combine existing and new posts
    all_posts = scheduled_posts + new_scheduled_posts
    
    # Save updated schedule
    with open('scheduled_posts.json', 'w') as f:
        json.dump({'schedule': all_posts}, f, indent=2)
    
    print(f"Added {len(new_scheduled_posts)} new posts to schedule")

if __name__ == "__main__":
    schedule_new_posts()

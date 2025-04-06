import tweepy, os, json, datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()
auth = tweepy.OAuthHandler(os.getenv("X_API_KEY"), os.getenv("X_API_SECRET"))
auth.set_access_token(os.getenv("X_ACCESS_TOKEN"), os.getenv("X_ACCESS_SECRET"))
api = tweepy.API(auth)
scheduler = BlockingScheduler()

def post(post_content):
    api.update_status(post_content)
    print(f"Posted: {post_content}")

def get_manual_posts():
    posts = []
    print("\nEnter your posts (press Enter twice to finish):")
    while True:
        post = input("Enter post (or press Enter to finish): ").strip()
        if not post:
            break
        
        # Get scheduling time
        while True:
            try:
                hours = int(input("Hours from now to post (0-23): "))
                minutes = int(input("Minutes from now to post (0-59): "))
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    post_time = datetime.datetime.now() + datetime.timedelta(hours=hours, minutes=minutes)
                    posts.append({"content": post, "schedule_time": post_time})
                    break
                else:
                    print("Invalid time. Hours must be 0-23, minutes must be 0-59.")
            except ValueError:
                print("Please enter valid numbers.")
    
    return posts

def load_posts_from_json():
    try:
        with open("posts.json", "r") as f:
            data = json.load(f)
        return [{"content": post, "schedule_time": datetime.datetime.now() + datetime.timedelta(minutes=i*5)} 
                for i, post in enumerate(data.get("edited", []))]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def schedule():
    print("\nX Post Scheduler")
    print("===============")
    
    while True:
        choice = input("\nChoose input method:\n1. Enter posts manually\n2. Load from posts.json\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            posts = get_manual_posts()
            break
        elif choice == "2":
            posts = load_posts_from_json()
            if not posts:
                print("No posts found in posts.json or file is invalid.")
                continue
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")
    
    if not posts:
        print("No posts to schedule. Exiting.")
        return
    
    print("\nScheduled posts:")
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. Post: {post['content']}")
        print(f"   Scheduled for: {post['schedule_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        scheduler.add_job(post, "date", run_date=post['schedule_time'], args=[post['content']])
    
    print("\nStarting scheduler. Press Ctrl+C to exit.")
    scheduler.start()

if __name__ == "__main__":
    schedule()

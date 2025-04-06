import json
import random
from datetime import datetime, timedelta
import pytz
import tweepy
import os
from dotenv import load_dotenv
import csv

# Load environment variables
os.environ.clear()
load_dotenv(override=True)

class SmartScheduler:
    def __init__(self):
        # Initialize Twitter API v2 client
        self.client = tweepy.Client(
            consumer_key=os.getenv('X_API_KEY'),
            consumer_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
            wait_on_rate_limit=True
        )
        
        # Load posts from JSON
        with open('posts.json', 'r') as f:
            self.posts = json.load(f)['edited']
        
        # Set up timezone for US Eastern Time
        self.timezone = pytz.timezone('America/New_York')
        
        # Initialize posting schedule
        self.schedule = []
    
    def get_current_est_time(self):
        """Get current time in US Eastern Time."""
        return datetime.now(self.timezone)
    
    def is_valid_posting_time(self, time):
        """Check if the given time is within valid posting hours (7 AM to 10 PM EST)."""
        return 7 <= time.hour <= 22
    
    def generate_posting_times(self, date, num_posts):
        """Generate random posting times for a given date."""
        times = []
        
        # Define peak hours (9-11 AM and 7-9 PM EST)
        morning_peak = (9, 11)
        evening_peak = (19, 21)
        
        # Distribute posts between peak and non-peak hours
        peak_posts = int(num_posts * 0.6)  # 60% of posts during peak hours
        non_peak_posts = num_posts - peak_posts
        
        # Generate times for peak hours
        for _ in range(peak_posts):
            if random.random() < 0.5:  # 50% chance for morning or evening
                hour = random.randint(morning_peak[0], morning_peak[1])
            else:
                hour = random.randint(evening_peak[0], evening_peak[1])
            minute = random.randint(0, 59)
            times.append(date.replace(hour=hour, minute=minute))
        
        # Generate times for non-peak hours
        valid_hours = list(range(7, 9)) + list(range(11, 19)) + list(range(21, 23))
        for _ in range(non_peak_posts):
            hour = random.choice(valid_hours)
            minute = random.randint(0, 59)
            times.append(date.replace(hour=hour, minute=minute))
        
        return sorted(times)
    
    def generate_natural_schedule(self):
        """Generate a natural posting schedule for all available posts."""
        schedule = []
        current_time = self.get_current_est_time()
        total_posts = len(self.posts)
        
        # Calculate how many days we need based on posting 2-5 posts per day
        avg_posts_per_day = 3.5  # average between 2 and 5
        estimated_days = max(1, int(total_posts / avg_posts_per_day))
        
        for day in range(estimated_days):
            target_date = current_time + timedelta(days=day)
            
            # For the last day, adjust num_posts to use remaining posts
            remaining_posts = len(self.posts)
            if day == estimated_days - 1:
                num_posts = remaining_posts
            else:
                # Randomly decide number of posts for the day (2-5 posts)
                num_posts = min(random.randint(2, 5), remaining_posts)
            
            # Generate posting times for the day
            posting_times = self.generate_posting_times(target_date, num_posts)
            
            # Add posts to schedule
            for post_time in posting_times:
                if len(self.posts) > 0:  # Check if we have posts available
                    post = random.choice(self.posts)
                    self.posts.remove(post)  # Remove used post
                    schedule.append({
                        'time': post_time,
                        'content': post
                    })
        
        self.schedule = sorted(schedule, key=lambda x: x['time'])
        return self.schedule
    
    def save_schedule(self, output_format='both'):
        """Save the schedule to files in CSV and JSON formats."""
        if not self.schedule:
            print("No schedule generated. Call generate_natural_schedule() first.")
            return
        
        # Save as CSV (good for importing into other tools)
        if output_format in ['csv', 'both']:
            csv_file = 'scheduled_posts.csv'
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Scheduled Time (EST)', 'Content'])
                for post in self.schedule:
                    writer.writerow([
                        post['time'].strftime('%Y-%m-%d %H:%M:%S'),
                        post['content']
                    ])
            print(f"\nSchedule saved to {csv_file}")
        
        # Save as JSON (good for programmatic access)
        if output_format in ['json', 'both']:
            json_file = 'scheduled_posts.json'
            with open(json_file, 'w') as f:
                json.dump({
                    'schedule': [{
                        'time': post['time'].strftime('%Y-%m-%d %H:%M:%S'),
                        'content': post['content']
                    } for post in self.schedule]
                }, f, indent=2)
            print(f"Schedule saved to {json_file}")
    
    def preview_schedule(self):
        """Preview the generated schedule."""
        if not self.schedule:
            print("No schedule generated. Call generate_natural_schedule() first.")
            return
        
        print("\nScheduled Posts Preview:")
        print("-" * 50)
        
        current_date = None
        for post in self.schedule:
            post_time = post['time']
            content = post['content']
            
            # Print date header if it's a new date
            post_date = post_time.strftime('%Y-%m-%d')
            if post_date != current_date:
                current_date = post_date
                print(f"\n{post_time.strftime('%A, %B %d, %Y')}:")
            
            # Print post details
            print(f"\n  {post_time.strftime('%I:%M %p')} EST")
            print(f"  {content}")
        
        print("\n" + "-" * 50)
        print(f"Total posts scheduled: {len(self.schedule)}")

if __name__ == "__main__":
    print("Bitcoin Post Scheduler (US Eastern Time)")
    print("=" * 40)
    
    scheduler = SmartScheduler()
    
    # Generate and preview schedule
    print("\nGenerating natural posting schedule...")
    scheduler.generate_natural_schedule()
    scheduler.preview_schedule()
    
    # Save schedule to files
    print("\nSaving schedule to files...")
    scheduler.save_schedule()
    
    print("\nDone! You can now use these files to set up automated posting:")
    print("1. scheduled_posts.csv - Import into scheduling tools")
    print("2. scheduled_posts.json - Use with automation scripts")
    print("\nTip: Use GitHub Actions or a cloud scheduler to handle the actual posting.")

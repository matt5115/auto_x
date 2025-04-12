import json
import datetime
import os
from random import randint

# Predefined Bitcoin posts
BITCOIN_POSTS = [
    "I've seen a lot of fear out there. But I'm not selling. Bitcoin's my long game—tariffs and headlines don't shake that.",
    "I bought some Bitcoin today. Worst case? I learn. Best case? I got in before the crowd.",
    "Friendly reminder: exchanges aren't your wallet. I moved mine off today. Control matters.",
    "My bank doesn't care if I win or lose. But Bitcoin? That's in *my* hands—if I hold the keys.",
    "Look around—chaos everywhere. But Bitcoin? Still standing strong. That says a lot.",
    "Bitcoin just keeps going. It's quiet, but powerful. I'm not sleeping on it.",
    "Why am I stacking Bitcoin instead of dollars? Because it actually *holds* value.",
    "I don't see Bitcoin as risky. I see it as protection. Against a system that's not working.",
    "Bitcoin's flowing off exchanges lately. I'm doing the same. Cold storage = peace of mind.",
    "While the old system scrambles, Bitcoin keeps doing what it's designed to do. I'm here for that.",
    "I've said it before—if your Bitcoin's on an exchange, it's not really yours. Learned that the hard way once.",
    "I missed the hedge last year. Not this time. Bitcoin's my play.",
    "Some folks are panic-selling. I'm zooming out. Bitcoin's still outperforming.",
    "They called Bitcoin a Ponzi. I call it the exit from one.",
    "I trust exchanges less every day. Took mine off today. Tick… tick…",
    "HODLing isn't about faith. It's about math—and I like the odds.",
    "People say Bitcoin is hype. I say it's gravity. The system's falling—Bitcoin isn't.",
    "Watching my savings get eaten by inflation hurt. Bitcoin's my freezer now.",
    "Honestly? If I had to bet on one thing in this mess, it's Bitcoin.",
    "Stocks make me dizzy. Bitcoin feels like a straight climb.",
    "Trust me on this: no one's coming to save your Bitcoin on an exchange. Get your keys.",
    "Bitcoin's not for everyone. But if you're looking ahead, it starts to make sense.",
    "Don't wait for the crash. That's what I used to do. Bitcoin taught me to be early.",
    "This isn't a hype train. It's a life raft. I grabbed it—still room left.",
    "I stopped letting headlines shake me. Bitcoin's built for storms.",
    "I don't see Bitcoin as optional anymore. It's a must-have in this economy.",
    "I'm holding my Bitcoin close. Because if I don't, someone else will."
]

def ensure_file_exists(filepath, default_content):
    """Create file with default content if it doesn't exist"""
    try:
        if not os.path.exists(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(default_content, f, indent=2)
            print(f"Created new file: {filepath}")
    except Exception as e:
        print(f"Warning: Could not create {filepath}: {str(e)}")

def get_random_posts(num_posts=1):
    """Get random posts from the predefined list"""
    selected_posts = []
    available_posts = BITCOIN_POSTS.copy()
    
    for _ in range(min(num_posts, len(available_posts))):
        if not available_posts:
            break
        index = randint(0, len(available_posts) - 1)
        selected_posts.append(available_posts.pop(index))
    
    return selected_posts

def save_to_markdown(posts):
    """Save posts to markdown file"""
    try:
        timestamp = datetime.datetime.now().isoformat()
        content = f"# Generated Bitcoin Posts\n\n## Posts Generated at {timestamp}\n\n"
        
        for i, post in enumerate(posts, 1):
            content += f"### {i}. Tweet\n```\n{post}\n```\n"
            content += f"Characters: {len(post)}\n\n"
        
        with open('generated_posts.md', 'w') as f:
            f.write(content)
        print("Successfully saved to generated_posts.md")
    except Exception as e:
        print(f"Warning: Could not save to markdown: {str(e)}")

def save_raw_posts(posts):
    """Save posts to raw_posts.json"""
    try:
        timestamp = datetime.datetime.now().isoformat()
        new_posts = []
        
        for post in posts:
            new_posts.append({
                'content': post,
                'category': 'bitcoin',
                'timestamp': timestamp,
                'characters': len(post)
            })
        
        # Load existing posts if available
        try:
            with open('raw_posts.json', 'r') as f:
                data = json.load(f)
                existing_posts = data.get('raw_posts', [])
        except (FileNotFoundError, json.JSONDecodeError):
            existing_posts = []
        
        # Combine and save
        all_posts = existing_posts + new_posts
        with open('raw_posts.json', 'w') as f:
            json.dump({'raw_posts': all_posts}, f, indent=2)
        print(f"Successfully saved {len(new_posts)} new posts to raw_posts.json")
    except Exception as e:
        print(f"Warning: Could not save to raw_posts.json: {str(e)}")

def run_content_creator(num_posts=1):
    """Main function to create and save posts"""
    try:
        # Ensure files exist
        ensure_file_exists('raw_posts.json', {'raw_posts': []})
        ensure_file_exists('generated_posts.md', '')
        
        # Get random posts
        posts = get_random_posts(num_posts)
        if not posts:
            print("Error: No posts generated")
            return
        
        # Save posts
        save_raw_posts(posts)
        save_to_markdown(posts)
        
        print("Content creation completed successfully")
    except Exception as e:
        print(f"Error in content creation: {str(e)}")

if __name__ == "__main__":
    run_content_creator(num_posts=1)

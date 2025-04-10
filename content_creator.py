import json
from openai import OpenAI
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

RESEARCH_FILE = "research_agent_output.json"
OUTPUT_FILE = "raw_posts.json"
MARKDOWN_FILE = "generated_posts.md"

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


def extract_categories(insights_text):
    """Extract unique categories from insights"""
    categories = set()
    lines = insights_text.split('\n')
    for line in lines:
        if line.strip().startswith('- Category:'):
            category = line.split(':', 1)[1].strip()
            categories.add(category)
    return list(categories)


def load_research_data(filename=RESEARCH_FILE):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        # Get the most recent insights
        insights = data.get("insights", [])
        if not insights:
            print(f"Error: No insights found in {filename}")
            return "", []
        latest_insight = insights[-1]  # Get the most recent insight
        categories = extract_categories(latest_insight["content"])
        return latest_insight["content"], categories
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return "", []
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error reading {filename}: {str(e)}")
        return "", []


def save_to_markdown(posts_by_category):
    timestamp = datetime.datetime.now().isoformat()
    
    # Load existing content if file exists
    try:
        with open(MARKDOWN_FILE, "r") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = "# Generated Bitcoin Posts\n\n"
    
    # Prepare new content
    new_content = f"\n## Posts Generated at {timestamp}\n\n"
    
    for category, posts in posts_by_category.items():
        new_content += f"### Category: {category}\n\n"
        for i, post in enumerate(posts, 1):
            new_content += f"#### {i}. Tweet\n"
            new_content += f"```\n{post}\n```\n"
            new_content += f"Characters: {len(post)}\n\n"
    
    # Combine and write content
    with open(MARKDOWN_FILE, "w") as f:
        f.write(existing_content + new_content)
    print(f"Added posts to {MARKDOWN_FILE}")


def save_raw_posts(posts_by_category):
    # Load existing posts if available
    try:
        with open(OUTPUT_FILE, "r") as f:
            data = json.load(f)
            existing_posts = data.get("raw_posts", [])
    except (FileNotFoundError, json.JSONDecodeError):
        existing_posts = []
    
    # Add timestamp to new posts
    timestamp = datetime.datetime.now().isoformat()
    new_posts = []
    
    for category, posts in posts_by_category.items():
        for post in posts:
            new_posts.append({
                "content": post,
                "category": category,
                "timestamp": timestamp,
                "characters": len(post)
            })
    
    # Combine and save
    all_posts = existing_posts + new_posts
    with open(OUTPUT_FILE, "w") as f:
        json.dump({"raw_posts": all_posts}, f, indent=4)
    print(f"Saved {len(new_posts)} new posts to {OUTPUT_FILE}")


def create_posts_for_category(insights_text, category, num_posts=1):
    """
    If category is 'bitcoin', returns a predefined post.
    Otherwise, generates posts using GPT-4.
    """
    if category.lower() == 'bitcoin':
        # Get a single post from the predefined list based on timestamp
        current_time = datetime.datetime.now()
        index = int(current_time.timestamp()) % len(BITCOIN_POSTS)
        return [BITCOIN_POSTS[index]]
    
    prompt = f"""
You are a Bitcoin content creator. Generate {num_posts} unique, original X (Twitter) posts focused on the category: {category}.

Each post must:
- Be under 280 characters
- Be focused specifically on the {category} aspect of Bitcoin
- Be informative and engaging
- NOT promote any books or products
- NOT use hashtags
- Be factual and educational
- Vary in style (questions, statements, insights, etc.)

Use the insights below for inspiration and factual basis, but create original content:

{insights_text}

Respond ONLY with a numbered list of X posts, nothing else.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=1000
    )

    output = response.choices[0].message.content
    posts = [line.strip("0123456789. ") for line in output.split("\n") if line.strip()]
    posts = [p for p in posts if 0 < len(p) <= 280]
    return posts


def run_content_creator(num_posts_per_category=1):
    insights_text, categories = load_research_data()
    if not insights_text or not categories:
        return
    
    posts_by_category = {}
    for category in categories:
        category_posts = create_posts_for_category(insights_text, category, num_posts_per_category)
        if category_posts:
            posts_by_category[category] = category_posts
    
    save_raw_posts(posts_by_category)
    save_to_markdown(posts_by_category)


if __name__ == "__main__":
    run_content_creator(num_posts_per_category=1)

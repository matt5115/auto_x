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


def create_posts_for_category(insights_text, category, num_posts=2):
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


def run_content_creator(num_posts_per_category=2):
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
    run_content_creator(num_posts_per_category=2)

import json
from openai import OpenAI
from dotenv import load_dotenv
import os
import datetime
import argparse
import re

load_dotenv(dotenv_path='/Users/matthew/CascadeProjects/Xagents/.env')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RAW_POSTS_FILE = "raw_posts.json"
EDITED_POSTS_FILE = "edited_posts.json"
MARKDOWN_FILE = "edited_posts.md"

def load_raw_posts():
    """Load posts from raw_posts.json, maintaining category structure"""
    try:
        with open(RAW_POSTS_FILE, "r") as f:
            data = json.load(f)
            return data.get("raw_posts", [])
    except FileNotFoundError:
        print(f"Error: {RAW_POSTS_FILE} not found.")
        return []

def clean_tweet(tweet, allow_emojis=False):
    """Clean a tweet by removing quotes, hashtags, and optionally emojis"""
    if ":" in tweet and '"' in tweet and any(char.isupper() for char in tweet.split(":")[0]):
        # This looks like a person quote (e.g., "Satoshi Nakamoto: 'quote'"), keep it
        return tweet
    
    # Remove quotes
    cleaned = tweet.replace('"', '').replace('"', '').replace('"', '')
    cleaned = cleaned.replace(''', '').replace(''', '')
    
    # Remove hashtags
    cleaned = ' '.join(word for word in cleaned.split() if not word.startswith('#'))
    
    # Remove emojis if not allowed
    if not allow_emojis:
        # Remove emoji characters
        cleaned = re.sub(r'[\U0001F300-\U0001F9FF]', '', cleaned)
        # Remove specific emojis used in text form
        cleaned = re.sub(r':[a-zA-Z_]+:', '', cleaned)
    
    return cleaned.strip()

def punch_up_tweets(posts, allow_emojis=False):
    """Improve tweets while maintaining their category focus, with multiple tones"""
    # Define different tones to use
    tones = [
        "casual and engaging",
        "professional and educational",
        "thought-provoking and analytical",
        "enthusiastic and motivational"
    ]
    
    # Group posts by category for context-aware editing
    posts_by_category = {}
    for post in posts:
        category = post.get("category", "General")
        if category not in posts_by_category:
            posts_by_category[category] = []
        posts_by_category[category].append(post)
    
    improved_posts = []
    
    for category, category_posts in posts_by_category.items():
        for tone in tones:
            prompt = f"""
You are a professional Bitcoin content editor and viral content expert.

Your job is to review and improve the following {category}-focused X (Twitter) posts. For each post, ensure it:
- Is grammatically perfect
- Is punchy, natural, and Twitter-native
- Maintains a **{tone}** tone
- {'Stays focused on the ' + category + ' aspect of Bitcoin' if category != 'General' else 'Focuses on Bitcoin fundamentals'}
- Remains informative while being engaging
- DOES NOT use any emojis
- Stays under 280 characters
- Maintains the original message and intent
- Removes any book promotion or self-promotion
- REMOVES ALL HASHTAGS
- REMOVES ALL QUOTES unless directly quoting a specific person (then format as: Person Name: "quote")
- Uses natural language without artificial wrapping quotes

Do NOT rewrite completely — only improve for:
- Flow and clarity
- Engagement potential
- Grammar and punctuation
- Natural Twitter voice

Here are the {category} tweets:

""" + "\n".join([f"{i+1}. {post['content']}" for i, post in enumerate(category_posts)])

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )

            output = response.choices[0].message.content.strip().split("\n")
            edited_tweets = [line.lstrip("0123456789. ").strip() for line in output if line.strip()]
            
            # Clean up tweets
            cleaned_tweets = [clean_tweet(tweet, allow_emojis=False) for tweet in edited_tweets]
            
            # Create improved posts with metadata
            for i, edited_tweet in enumerate(cleaned_tweets):
                if len(edited_tweet) <= 280:  # Ensure tweet meets length requirement
                    original_post = category_posts[i]
                    improved_posts.append({
                        "content": edited_tweet,
                        "category": category,
                        "tone": tone,
                        "original_content": original_post["content"],
                        "timestamp": datetime.datetime.now().isoformat(),
                        "characters": len(edited_tweet),
                        "engagement_score": calculate_engagement_score(edited_tweet)
                    })
    
    return improved_posts

def calculate_engagement_score(tweet):
    """Calculate an engagement potential score based on various factors"""
    prompt = f"""
Rate this tweet's engagement potential from 1-100 based on:
- Clarity (20 points)
- Memorability (20 points)
- Educational Value (20 points)
- Emotional Appeal (20 points)
- Call to Action (20 points)

Tweet: {tweet}

Respond with ONLY a number 1-100.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )
        score = int(response.choices[0].message.content.strip())
        return min(max(score, 1), 100)  # Ensure score is between 1-100
    except:
        return 70  # Default score if scoring fails

def save_edited_posts(posts):
    """Save edited posts to JSON and markdown files"""
    # Save to JSON
    with open(EDITED_POSTS_FILE, "w") as f:
        json.dump({"edited_posts": posts}, f, indent=2)
    
    # Save to markdown
    with open(MARKDOWN_FILE, "w") as f:
        f.write("# Edited Bitcoin Posts\n\n")
        f.write(f"## Posts Edited at {datetime.datetime.now().isoformat()}\n\n")
        
        # Group by category and tone
        posts_by_category = {}
        for post in posts:
            category = post["category"]
            if category not in posts_by_category:
                posts_by_category[category] = {}
            
            tone = post["tone"]
            if tone not in posts_by_category[category]:
                posts_by_category[category][tone] = []
            
            posts_by_category[category][tone].append(post)
        
        # Write posts grouped by category and tone
        for category, tones in posts_by_category.items():
            f.write(f"### Category: {category}\n\n")
            for tone, tone_posts in tones.items():
                f.write(f"#### Tone: {tone}\n\n")
                for i, post in enumerate(tone_posts, 1):
                    f.write(f"##### {i}. Tweet (Score: {post['engagement_score']})\n")
                    f.write("```\n")
                    f.write(f"EDITED: {post['content']}\n")
                    f.write(f"ORIGINAL: {post['original_content']}\n")
                    f.write("```\n")
                    f.write(f"Characters: {post['characters']}\n\n")
    
    print(f"Saved {len(posts)} edited posts to {EDITED_POSTS_FILE}")
    print(f"Added edited posts to {MARKDOWN_FILE}")

def run_editor(allow_emojis=False):
    """Main function to run the editor"""
    raw = load_raw_posts()
    if not raw:
        print("No raw posts found.")
        return
    
    edited = punch_up_tweets(raw, allow_emojis)
    save_edited_posts(edited)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edit and improve Bitcoin-focused tweets")
    parser.add_argument("--emojis", action="store_true",
                      help="Allow emojis in tweets")
    
    args = parser.parse_args()
    run_editor(allow_emojis=args.emojis)

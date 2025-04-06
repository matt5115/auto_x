from dotenv import load_dotenv
import os
import json
import datetime
from openai import OpenAI

# Load environment variables
load_dotenv(dotenv_path='/Users/matthew/CascadeProjects/Xagents/.env')
openai_api_key = os.getenv("OPENAI_API_KEY")

# Constants
BOOK_PATH = "/Users/matthew/CascadeProjects/Xagents/sources/full_book.txt"
TWEETS_FILE = "tweets.json"
INSIGHTS_OUTPUT = "research_agent_output.json"
INSIGHTS_MARKDOWN = "research_insights.md"

def load_book(path=BOOK_PATH):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Book file not found at {path}")
        return ""

def load_tweets(filename=TWEETS_FILE):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Tweets file not found at {filename}")
        return {}

def save_insights_markdown(insight_data, tweets_dict):
    timestamp = insight_data["timestamp"]
    content = insight_data["content"]
    sources = insight_data["sources"]
    
    # Load existing content if file exists
    try:
        with open(INSIGHTS_MARKDOWN, "r") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = "# Bitcoin Research Insights\n\n"
    
    # Format new content
    new_content = f"\n## Research Batch - {timestamp}\n\n"
    
    # Add source information
    new_content += "### Source Information\n"
    new_content += f"- **Twitter Accounts Analyzed:** {', '.join(sources['users'])}\n"
    new_content += f"- **Total Tweets Analyzed:** {sources['tweet_count']}\n"
    new_content += f"- **Book Excerpt Length:** {sources['book_excerpt_length']} characters\n\n"
    
    # Process the content
    lines = content.split('\n')
    current_insight = {}
    insights = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            # Parse metadata lines
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip('- ')
                value = parts[1].strip()
                current_insight[key] = value
        elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            # New insight starts
            if current_insight:
                insights.append(current_insight)
            current_insight = {}
        elif line.startswith('Summary:'):
            # Process the last insight if any
            if current_insight:
                insights.append(current_insight)
            # Add summary section
            new_content += "### Summary\n"
            summary_lines = [l.strip('- ') for l in lines[lines.index(line)+1:] if l.strip().startswith('-')]
            new_content += '\n'.join(f"- {line}" for line in summary_lines)
            break
    
    # Add insights
    new_content += "\n### Insights\n\n"
    for i, insight in enumerate(insights, 1):
        if not insight:  # Skip empty insights
            continue
        new_content += f"#### {i}. {insight.get('Category', 'Uncategorized')}\n"
        new_content += f"- **Content:** {insight.get('Content', '')}\n"
        new_content += f"- **Source:** {insight.get('Source', '')}\n"
        new_content += f"- **Tone:** {insight.get('Tone', '')}\n"
        new_content += f"- **Format Style:** {insight.get('Format Style', '')}\n"
        new_content += f"- **Target Audience:** {insight.get('Target Audience', '')}\n\n"
    
    # Write the combined content
    with open(INSIGHTS_MARKDOWN, "w") as f:
        f.write(existing_content + new_content)
    
    print(f"Added new research insights to {INSIGHTS_MARKDOWN}")

def generate_insights(tweets_dict, book_text):
    # Trim book text if needed
    max_book_chars = 6000  # Reduced from 10000 to stay within token limits
    trimmed_book_text = book_text[:max_book_chars] + ("..." if len(book_text) > max_book_chars else "")
    
    # Prepare tweet texts (limit tweets per user)
    max_tweets_per_user = 5
    tweet_texts = []
    for username, tweets in tweets_dict.items():
        user_tweets = [t.get('text', '') for t in tweets[:max_tweets_per_user]]
        if user_tweets:
            tweet_texts.append(f"@{username}:\n" + "\n".join(user_tweets))
    tweet_text_combined = "\n\n".join(tweet_texts)

    prompt = (
        "You are a Bitcoin content research agent. Analyze the provided book content and tweets.\n\n"
        "Focus on:\n"
        "1. Book Content (80%)\n"
        "2. Bitcoin-related Tweets (20%)\n\n"
        "Return a structured list of tweetable insights with the following metadata for each:\n\n"
        "- Content: (the tweetable idea)\n"
        "- Source: (Book / Tweet + chapter or handle)\n"
        "- Category: (auto-created based on recurring themes, max 10)\n"
        "- Tone: (e.g., Inspiring, Educational, Sarcastic)\n"
        "- Format Style: (Thread, Meme Idea, Punchline, Quote, Question, CTA)\n"
        "- Target Audience: (e.g., Normies, Traders, Bitcoiners)\n\n"
        "Also include a final summary listing the categories found and their purpose.\n\n"
        "----\n"
        f"BOOK CONTENT:\n{trimmed_book_text}\n\n"
        "----\n"
        f"TWEETS:\n{tweet_text_combined}\n"
    )

    openai_client = OpenAI(api_key=openai_api_key)
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000  # Reduced from 4000
    )

    feedback = response.choices[0].message.content.strip()
    
    # Load existing insights if available
    try:
        with open(INSIGHTS_OUTPUT, "r") as f:
            data = json.load(f)
            insights = data.get("insights", [])
    except (FileNotFoundError, json.JSONDecodeError):
        insights = []
    
    # Add new insights with timestamp
    new_insight = {
        "timestamp": datetime.datetime.now().isoformat(),
        "content": feedback,
        "sources": {
            "users": list(tweets_dict.keys()),
            "tweet_count": sum(len(tweets[:max_tweets_per_user]) for tweets in tweets_dict.values()),
            "book_excerpt_length": len(trimmed_book_text)
        }
    }
    insights.append(new_insight)
    
    # Save updated insights to JSON
    with open(INSIGHTS_OUTPUT, "w") as f:
        json.dump({"insights": insights}, f, indent=4)
    print(f"Added new insights to {INSIGHTS_OUTPUT}")
    
    # Save insights to markdown
    save_insights_markdown(new_insight, tweets_dict)
    
    return feedback

if __name__ == "__main__":
    book = load_book()
    if not book:
        print("Error: Could not load book content")
        exit(1)
        
    tweets = load_tweets()
    if not tweets:
        print("Error: Could not load tweets")
        exit(1)
        
    generate_insights(tweets, book)

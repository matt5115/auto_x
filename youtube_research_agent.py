import os
import json
from dotenv import load_dotenv
from googleapiclient.discovery import build
from openai import OpenAI
import datetime

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
BOOK_PATH = "/Users/matthew/CascadeProjects/Xagents/sources/full_book.txt"
OUTPUT_FILE = "youtube_research_output.json"

# Initialize YouTube client if API key is available
youtube = None
try:
    if YOUTUBE_API_KEY:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
except Exception as e:
    print(f"Warning: YouTube API initialization failed: {str(e)}")

def load_book(path=BOOK_PATH):
    """Load the book content from the specified path"""
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Book not found at {path}")
        return ""

def get_videos(channel_id, max_results=5):
    """Fetch recent videos from a YouTube channel"""
    if youtube is None:
        print("Error: YouTube API is not initialized")
        return []
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=max_results,
        order="date",
        type="video"
    )
    response = request.execute()
    return [
        {
            "videoId": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "publishedAt": item["snippet"]["publishedAt"]
        }
        for item in response.get("items", [])
    ]

def get_comments(video_id, max_comments=20):
    """Fetch top comments from a YouTube video"""
    if youtube is None:
        print("Error: YouTube API is not initialized")
        return []
    comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_comments, 100),
            textFormat="plainText"
        )
        response = request.execute()
        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": comment["textDisplay"],
                "likeCount": comment["likeCount"],
                "publishedAt": comment["publishedAt"]
            })
    except Exception as e:
        print(f"Error fetching comments for video {video_id}: {str(e)}")
    return comments

def compile_youtube_data(channel_ids):
    """Compile video and comment data from multiple channels"""
    all_data = []
    for channel_id in channel_ids:
        try:
            videos = get_videos(channel_id)
            for video in videos:
                comments = get_comments(video["videoId"])
                video["comments"] = comments
                all_data.append(video)
        except Exception as e:
            print(f"Error processing channel {channel_id}: {str(e)}")
    return all_data

def analyze_youtube_and_book(book_text, youtube_data):
    """Analyze book and YouTube content to generate insights"""
    # Prepare YouTube data for analysis
    yt_texts = []
    for video in youtube_data:
        video_text = f"Title: {video['title']}\nDescription: {video['description']}\nComments:\n"
        comment_texts = [f"- {c['text']} (Likes: {c['likeCount']})" for c in video["comments"]]
        video_text += "\n".join(comment_texts)
        yt_texts.append(video_text)
    
    yt_content = "\n\n".join(yt_texts)
    
    # Trim book text if too long while preserving context
    max_book_chars = 10000
    trimmed_book = book_text[:max_book_chars] + ("..." if len(book_text) > max_book_chars else "")

    prompt = f"""
You are a Bitcoin research agent analyzing content for social media insights.

Review the following Bitcoin-related content:
1. A book about Bitcoin
2. YouTube video data (titles, descriptions, and comments)

For each meaningful insight, provide:
1. Content: A tweetable insight (max 280 chars)
2. Source: Book section or YouTube video title
3. Category: One of these categories:
   - Technical Analysis
   - Investment Strategy
   - Bitcoin Philosophy
   - Market Commentary
   - Educational
   - News & Updates
   - Community Insights
   - Success Stories
   - Risk Management
   - Adoption Trends
4. Tone: The emotional tone (e.g., Inspiring, Educational, Skeptical)
5. Format: Content format (e.g., Question, Statistic, Quote, Call-to-Action)
6. Audience: Target demographic (e.g., Beginners, Traders, Developers)

Then provide a summary of:
1. Most common themes and patterns
2. Engagement patterns (what gets the most likes/comments)
3. Content gaps and opportunities
4. Recommended content strategy

==== BOOK EXCERPT ====
{trimmed_book}

==== YOUTUBE CONTENT ====
{yt_content}
"""

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4000
    )

    result = response.choices[0].message.content.strip()
    
    # Save results with metadata
    output_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "analysis": result,
        "metadata": {
            "channels_analyzed": len(youtube_data),
            "videos_analyzed": len(youtube_data),
            "total_comments": sum(len(v["comments"]) for v in youtube_data),
            "book_chars_analyzed": len(trimmed_book)
        }
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved research insights to {OUTPUT_FILE}")
    return result

def run_youtube_agent(channel_ids):
    """Main function to run the YouTube research agent"""
    print("Loading book content...")
    book_text = load_book()
    
    print("Fetching YouTube data...")
    youtube_data = compile_youtube_data(channel_ids)
    
    if book_text and youtube_data:
        print("Analyzing content...")
        analyze_youtube_and_book(book_text, youtube_data)
    else:
        print("Error: Missing book content or YouTube data")

if __name__ == "__main__":
    # Popular Bitcoin YouTube channels
    bitcoin_channels = [
        "UCtPzCG7PntgrC8Qy0fX0r2A",  # Swan Bitcoin
        "UCJWCJCWOxBYSi5DhCieLOLQ",  # BTC Sessions
        "UCzWQJUv1xW2bJ5Q1mJ1jSBA"   # What Bitcoin Did
    ]
    run_youtube_agent(bitcoin_channels)

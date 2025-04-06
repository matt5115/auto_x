import json
import os
import datetime
import tweepy
from googleapiclient.discovery import build
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI()
bearer_token = os.getenv("X_BEARER_TOKEN")
youtube_api_key = os.getenv("YOUTUBE_API_KEY")
client = tweepy.Client(bearer_token=bearer_token)

# Initialize YouTube client only when needed
youtube_client = None

def get_youtube_client():
    """Get or initialize the YouTube client."""
    global youtube_client
    if youtube_client is None:
        if not youtube_api_key:
            raise ValueError("YouTube API key not found in environment variables")
        youtube_client = build("youtube", "v3", developerKey=youtube_api_key)
    return youtube_client

def load_target_accounts(filename="target_accounts.json"):
    """Load target accounts from JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f).get("target_accounts", [])
    except FileNotFoundError:
        print(f"Error: {filename} not found. Using defaults.")
        return [{"platform": "X", "name": "rajatsonifnance"}, {"platform": "X", "name": "Bitcoin_Teddy"}]

def download_x_tweets(username, max_tweets=10):
    """Download tweets from a X user."""
    try:
        user = client.get_user(username=username)
        tweets = client.get_users_tweets(
            id=user.data.id,
            max_results=min(max_tweets, 100),
            tweet_fields=["created_at", "text", "public_metrics"]
        )
        return [{
            "text": tweet.text,
            "id": str(tweet.id),
            "created_at": str(tweet.created_at),
            "metrics": tweet.public_metrics
        } for tweet in tweets.data or []]
    except Exception as e:
        print(f"Error fetching X {username}: {e}")
        return []

def download_youtube_videos(channel_name, max_videos=10):
    """Download video metadata from a YouTube channel."""
    try:
        client = get_youtube_client()
    except ValueError as e:
        print(f"YouTube API error: {e}")
        return []
        
    try:
        search_response = client.search().list(q=channel_name, type="channel", part="id").execute()
        channel_id = search_response["items"][0]["id"]["channelId"]
        videos = client.search().list(
            channelId=channel_id,
            part="snippet",
            maxResults=max_videos,
            type="video",
            order="date"
        ).execute()
        
        video_data = []
        for video in videos["items"]:
            video_id = video["id"]["videoId"]
            stats = client.videos().list(
                id=video_id,
                part="statistics"
            ).execute()["items"][0]["statistics"]
            
            video_data.append({
                "title": video["snippet"]["title"],
                "description": video["snippet"]["description"],
                "id": video_id,
                "published_at": video["snippet"]["publishedAt"],
                "metrics": {
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0))
                }
            })
        return video_data
    except Exception as e:
        print(f"Error fetching YouTube {channel_name}: {e}")
        return []

def save_content(target_accounts):
    """Download and save content from all target accounts."""
    all_content = {"X": {}, "YouTube": {}}
    
    for acc in target_accounts:
        if acc["platform"] == "X":
            tweets = download_x_tweets(acc["name"])
            if tweets:
                all_content["X"][acc["name"]] = tweets
        elif acc["platform"] == "YouTube":
            videos = download_youtube_videos(acc["name"])
            if videos:
                all_content["YouTube"][acc["name"]] = videos
    
    # Save X tweets
    with open("tweets.json", "w") as f:
        json.dump(all_content["X"], f, indent=4)
    print(f"Saved X tweets to tweets.json. Total: {sum(len(t) for t in all_content['X'].values())}")
    
    # Save YouTube data
    with open("youtube_data.json", "w") as f:
        json.dump(all_content["YouTube"], f, indent=4)
    print(f"Saved YouTube data to youtube_data.json. Total: {sum(len(v) for v in all_content['YouTube'].values())}")
    
    return all_content

def load_book(filename="my_book.txt"):
    """Load book content from file."""
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return ""

def get_chatgpt_feedback(content_dict, book_text):
    """Get ChatGPT's analysis of content and book text."""
    # Format X tweets
    x_texts = []
    for user, tweets in content_dict["X"].items():
        for t in tweets:
            metrics = t.get("metrics", {})
            engagement = f"[❤️ {metrics.get('like_count', 0):,} 🔄 {metrics.get('retweet_count', 0):,}]"
            x_texts.append(f"@{user}: {t['text']} {engagement}")
    
    # Format YouTube content
    yt_texts = []
    for channel, videos in content_dict["YouTube"].items():
        for v in videos:
            metrics = v.get("metrics", {})
            engagement = f"[👁️ {metrics.get('views', 0):,} 👍 {metrics.get('likes', 0):,}]"
            yt_texts.append(f"{channel}: {v['title']} - {v['description']} {engagement}")
    
    prompt = (
        "Analyze these X tweets and YouTube video details along with my book text below. "
        "Provide detailed feedback for my Content Creator Agent on how to generate engaging, thoughtful, funny, or memorable X posts "
        "(under 280 characters) that reflect my vision and goals of helping people, as stated in the book.\n\n"
        "Consider:\n"
        "1. Content types that perform well (educational, inspirational, humorous)\n"
        "2. Writing styles that drive engagement\n"
        "3. Common themes and topics that resonate with the audience\n"
        "4. Effective use of humor and storytelling\n"
        "5. Ways to adapt YouTube content into tweet format\n\n"
        f"X Tweets:\n{chr(10).join(x_texts[:50])}\n\n"  # Limit to 50 tweets
        f"YouTube Videos:\n{chr(10).join(yt_texts[:20])}\n\n"  # Limit to 20 videos
        f"Book Text:\n{book_text[:2000]}"  # Limit book text to avoid token limits
    )
    
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    feedback = response.choices[0].message.content
    
    with open("feedback.json", "w") as f:
        json.dump({"feedback": feedback}, f, indent=4)
    print("Saved ChatGPT feedback to feedback.json")
    return feedback

def check_credentials(target_accounts):
    """Check if required credentials are available for the target accounts."""
    platforms = {acc["platform"] for acc in target_accounts}
    
    if "X" in platforms and not bearer_token:
        print("Error: X_BEARER_TOKEN not found in environment variables")
        print("Please set up your X API credentials in the .env file:")
        print("X_BEARER_TOKEN=your_bearer_token")
        return False
    
    if "YouTube" in platforms and not youtube_api_key:
        print("Error: YOUTUBE_API_KEY not found in environment variables")
        print("Please set up your YouTube API credentials in the .env file:")
        print("YOUTUBE_API_KEY=your_api_key")
        return False
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please set up your OpenAI API key in the .env file:")
        print("OPENAI_API_KEY=your_api_key")
        return False
    
    return True

def run_research_agent():
    """Main function to run the research agent."""
    print("\nResearch Agent")
    print("-------------")
    target_accounts = load_target_accounts()
    if not target_accounts:
        print("No target accounts found.")
        return
    
    if not check_credentials(target_accounts):
        return
    
    try:
        content_dict = save_content(target_accounts)
        book_text = load_book()
        
        if content_dict and book_text:
            feedback = get_chatgpt_feedback(content_dict, book_text)
            print("\nAnalysis complete! Check feedback.json for detailed insights.")
            return feedback
    except Exception as e:
        print(f"Error: {e}")
        print("Please check your API credentials and try again.")

if __name__ == "__main__":
    run_research_agent()

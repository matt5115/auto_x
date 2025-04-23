from flask import Flask
import json
import tweepy
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
import threading
import time
import sys
from flask import render_template, request, jsonify
import openai

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

def post_due_tweets():
    while True:
        try:
            # Load environment variables
            load_dotenv()
            
            # Get current time in EST
            est = pytz.timezone('America/New_York')
            current_time = datetime.now(est)
            print(f"\nChecking for tweets at {current_time.strftime('%Y-%m-%d %H:%M:%S')} EST")
            
            # Load schedule
            try:
                with open('scheduled_posts.json', 'r') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading schedule: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
                continue
                
            # Find the earliest scheduled post that's due
            due_post = None
            earliest_time = None
            
            for post in data.get('schedule', []):
                try:
                    scheduled_time = datetime.strptime(post['time'], '%Y-%m-%d %H:%M:%S')
                    scheduled_time = est.localize(scheduled_time)
                    
                    if current_time >= scheduled_time and (earliest_time is None or scheduled_time < earliest_time):
                        due_post = post
                        earliest_time = scheduled_time
                except Exception as e:
                    print(f"Error processing post: {str(e)}")
                    continue
            
            # If we found a due post, post it
            if due_post:
                try:
                    # Initialize Twitter client
                    client = tweepy.Client(
                        consumer_key=os.getenv('X_API_KEY'),
                        consumer_secret=os.getenv('X_API_SECRET'),
                        access_token=os.getenv('X_ACCESS_TOKEN'),
                        access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
                        wait_on_rate_limit=True
                    )
                    
                    print(f"Posting tweet scheduled for {earliest_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    response = client.create_tweet(text=due_post['content'])
                    print(f"Successfully posted tweet at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Remove the posted tweet from schedule
                    data['schedule'] = [post for post in data['schedule'] if post != due_post]
                    with open('scheduled_posts.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print("Removed posted tweet from schedule")
                    
                except Exception as e:
                    print(f"Error posting tweet: {str(e)}")
            
            # Sleep for 1 minute before next check
            time.sleep(60)
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying

@app.route('/')
def home():
    return 'Tweet Scheduler is running'

@app.route('/health')
def health():
    return 'OK'

@app.route('/reply-generator')
def reply_generator():
    """Renders the Custom Tweet Reply Generator web interface."""
    return render_template('reply_generator.html')

@app.route('/api/generate-reply', methods=['POST'])
def generate_reply():
    """API endpoint to generate a reply to a tweet."""
    try:
        data = request.json
        tweet_text = data.get('tweet_text', '')
        tweet_url = data.get('tweet_url', '')
        selected_tones = data.get('tones', [])
        character_limit = data.get('character_limit', 280)
        
        # If URL is provided, try to fetch the tweet text
        if tweet_url and not tweet_text:
            # Initialize Twitter client
            client = tweepy.Client(
                bearer_token=os.getenv('X_BEARER_TOKEN'),
                wait_on_rate_limit=True
            )
            
            # Extract tweet ID from URL
            tweet_id = extract_tweet_id(tweet_url)
            if tweet_id:
                # Fetch tweet text
                tweet = client.get_tweet(tweet_id, tweet_fields=['text'])
                if tweet and tweet.data:
                    tweet_text = tweet.data.text
        
        # Generate reply based on the tweet text and selected tones
        if not tweet_text:
            return jsonify({
                'status': 'error',
                'message': 'No tweet text provided or could not fetch tweet from URL'
            }), 400
        
        # Generate the reply using predefined tones and Bitcoin voice
        reply = generate_bitcoin_reply(tweet_text, selected_tones, character_limit)
        
        return jsonify({
            'status': 'success',
            'reply': reply,
            'character_count': len(reply)
        })
    
    except Exception as e:
        print(f"Error generating reply: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error generating reply: {str(e)}'
        }), 500

def extract_tweet_id(url):
    """Extract tweet ID from a tweet URL."""
    try:
        # Handle both old and new Twitter URL formats
        if 'twitter.com' in url or 'x.com' in url:
            # Split by / and get the last part of the URL which should be the ID
            parts = url.strip().split('/')
            for i, part in enumerate(parts):
                if part == 'status' or part == 'statuses':
                    if i + 1 < len(parts):
                        # Return only the numeric part (remove any query parameters)
                        return parts[i + 1].split('?')[0]
        return None
    except Exception:
        return None

# Fixed Bitcoin voice directive
BITCOIN_VOICE_DIRECTIVE = (
    "You are a confident Bitcoin advocate with a snarky, witty, and intelligent tone. "
    "Central banks are out of runway, fiat is broken, and Bitcoin isn't a bet on price—it's an exit from a broken monetary system. "
    "Always reply with clarity, irreverence, and incisiveness."
)

# Mapping of tone options to supplemental instructions
TONE_MAPPING = {
    "intelligent": " Ensure your response is sharp and insightful.",
    "witty": " Inject clever wordplay and humor.",
    "snarky": " Reply with biting sarcasm and irreverence.",
    "formal": " Maintain an authoritative stance while still being direct and opinionated.",
    "casual": " Use conversational language while maintaining your strong Bitcoin perspective."
}

def build_bitcoin_prompt(tweet_text, selected_tones, char_limit=280):
    """
    Constructs a prompt for OpenAI API that ensures replies are in a distinctive Bitcoin voice.
    
    Args:
        tweet_text (str): The text of the tweet to reply to
        selected_tones (list): List of tone options selected by the user
        char_limit (int): Character limit for the reply
        
    Returns:
        str: A complete prompt with voice directive, tone enhancements, and context
    """
    # Start with the fixed Bitcoin voice directive
    prompt = BITCOIN_VOICE_DIRECTIVE
    
    # Add tone-specific enhancements
    for tone in selected_tones:
        prompt += TONE_MAPPING.get(tone.lower(), "")
    
    # Append direct reply instructions to ensure relevance and style
    additional_instructions = (
        " Reply directly to the tweet using your signature style. "
        "Your response should be a concise, opinionated retort that directly engages the tweet's message. "
        "Do not merely analyze or restate the tweet—deliver a clever, snarky comment that reflects your strong Bitcoin stance. "
        "Avoid generic financial language and buzzwords."
    )
    prompt += additional_instructions
    
    # Add character limit instruction
    prompt += f" Ensure the reply is under {char_limit} characters."
    
    # Add the tweet context with double quotes for clarity
    prompt += f"\n\nNow, provide a reply to the following tweet: \"{tweet_text}\""
    
    return prompt

def generate_bitcoin_reply(tweet_text, selected_tones, character_limit):
    """
    Generates a Bitcoin-centric reply to a tweet using OpenAI API.
    
    Args:
        tweet_text (str): The text of the tweet to reply to
        selected_tones (list): List of tone options selected by the user
        character_limit (int): Character limit for the reply
        
    Returns:
        str: Generated reply in Bitcoin voice with selected tones
    """
    # Build the prompt with Bitcoin voice and selected tones
    prompt = build_bitcoin_prompt(tweet_text, selected_tones, character_limit)
    
    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        # Extract and return the generated reply
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        # Fall back to template-based approach if API call fails
        return generate_template_reply(tweet_text, selected_tones, character_limit)

def generate_template_reply(tweet_text, selected_tones, character_limit):
    """
    Fallback function to generate replies using templates when API is unavailable.
    
    Args:
        tweet_text (str): The text of the tweet to reply to
        selected_tones (list): List of tone options selected by the user
        character_limit (int): Character limit for the reply
        
    Returns:
        str: Generated reply from templates
    """
    # Temporary solution: Enhanced template-based replies with Bitcoin focus
    bitcoin_templates = {
        "intelligent": [
            "While many see volatility, I see freedom in action. Bitcoin's path isn't straight, but neither was breaking away from the gold standard. Worth considering.",
            "Looking beyond the noise: Bitcoin solves the fundamental issue of monetary debasement. Your concerns about {topic} are precisely why we need hard money.",
            "The research is clear on this: as {topic} continues, Bitcoin's fixed supply becomes increasingly important. Not speculation—mathematical certainty."
        ],
        "witty": [
            "Central banks can print trillions, but they can't print my Bitcoin. Funny how {topic} always leads back to needing money they can't devalue!",
            "While everyone's distracted by {topic}, I'm stacking sats. Future generations will wonder why we ever trusted money created by committee.",
            "Bitcoin doesn't care about {topic}—and that's exactly why I care about Bitcoin. Funny how that works, isn't it?"
        ],
        "snarky": [
            "Oh look, more {topic} problems that mysteriously require printing money to fix. Meanwhile, my Bitcoin stays limited to 21 million. Ever. Weird coincidence.",
            "Sure, keep worrying about {topic} while your savings quietly evaporate. I'll be over here with my non-inflatable money, watching the show.",
            "They told us {topic} was under control too. Just like inflation was 'transitory'. My Bitcoin doesn't believe in fairy tales anymore."
        ],
        "formal": [
            "Given current monetary conditions and the concerns raised about {topic}, Bitcoin's role as a non-sovereign store of value warrants serious consideration.",
            "When evaluating {topic}, it's prudent to consider alternatives to the traditional financial framework. Bitcoin offers precisely such an alternative.",
            "The correlation between {topic} and monetary intervention is noteworthy. Bitcoin's design specifically addresses this systemic vulnerability."
        ],
        "casual": [
            "Yeah, {topic} is definitely concerning. That's exactly why I've been putting some money into Bitcoin—can't inflate it, can't seize it. Just makes sense.",
            "I hear you on {topic}! Been there. That's why Bitcoin clicked for me—it's just money that works without all the drama. Game-changer.",
            "Totally get the {topic} situation. Honestly, Bitcoin has been my peace of mind through all of this. No committees, no printers, just math."
        ]
    }
    
    # Default to intelligent if no valid tone is selected
    selected_tone = selected_tones[0].lower() if selected_tones and selected_tones[0].lower() in bitcoin_templates else "intelligent"
    
    # Extract a relevant topic from the tweet
    words = tweet_text.split()
    if len(words) > 5:
        topic = ' '.join(words[0:3])
    else:
        topic = tweet_text
    
    # Select a template and insert the topic
    import random
    templates = bitcoin_templates[selected_tone]
    template = random.choice(templates)
    reply = template.replace("{topic}", topic)
    
    # Ensure the reply is within the character limit
    if len(reply) > character_limit:
        reply = reply[:character_limit-3] + "..."
    
    return reply

def start_scheduler():
    scheduler_thread = threading.Thread(target=post_due_tweets)
    scheduler_thread.daemon = True
    scheduler_thread.start()

if __name__ == '__main__':
    # Start the scheduler in a separate thread
    start_scheduler()
    # Run the Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

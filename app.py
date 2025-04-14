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

app = Flask(__name__)

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
        
        # Generate the reply using predefined tones
        reply = generate_tweet_reply(tweet_text, selected_tones, character_limit)
        
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

def generate_tweet_reply(tweet_text, tones, character_limit):
    """Generate a reply based on the tweet text and selected tones."""
    # Define tone templates for replies
    tone_templates = {
        'intelligent': [
            "Interesting point. Have you considered {insight}?",
            "This is a thoughtful take. I'd add that {insight}.",
            "You raise a good issue. The research actually suggests {insight}."
        ],
        'witty': [
            "Haha, love this! And just imagine if {joke}...",
            "Well played! Though I can't help but think {joke}.",
            "That's one way to look at it 😂 Another might be {joke}."
        ],
        'snarky': [
            "Sure, if we're ignoring {contradiction}...",
            "Bold of you to assume {contradiction}.",
            "Oh sweet summer child... {contradiction}."
        ],
        'formal': [
            "I appreciate your perspective. However, {counterpoint}.",
            "Thank you for sharing. It's worth noting that {counterpoint}.",
            "While that's a valid observation, consider that {counterpoint}."
        ],
        'casual': [
            "Yeah I get that! But also {alternative}.",
            "Totally! And you know what else? {alternative}.",
            "Right? I was just thinking {alternative}."
        ]
    }
    
    # For now, use a very simple reply generation approach
    # In a production environment, you would likely use a more sophisticated AI model
    selected_tone = tones[0] if tones else 'intelligent'  # Default to intelligent if no tone selected
    
    # Simple logic to create a contextual placeholder based on the tweet
    words = tweet_text.split()
    if len(words) > 5:
        topic = ' '.join(words[0:3])
    else:
        topic = tweet_text
    
    # Use templates based on selected tone
    if selected_tone in tone_templates:
        templates = tone_templates[selected_tone]
        import random
        template = random.choice(templates)
        
        # Fill in the template with context from the tweet
        if '{insight}' in template:
            reply = template.replace('{insight}', f"looking at {topic} from a different perspective")
        elif '{joke}' in template:
            reply = template.replace('{joke}', f"everyone started talking about {topic} like that")
        elif '{contradiction}' in template:
            reply = template.replace('{contradiction}', f"that {topic} has more nuance")
        elif '{counterpoint}' in template:
            reply = template.replace('{counterpoint}', f"research on {topic} suggests otherwise")
        elif '{alternative}' in template:
            reply = template.replace('{alternative}', f"I've been thinking about {topic} too")
        else:
            reply = template
    else:
        reply = f"Interesting tweet about {topic}. Thanks for sharing!"
    
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

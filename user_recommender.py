import tweepy
from openai import OpenAI
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables with override
load_dotenv(override=True)

# Get API keys
openai_api_key = os.getenv("OPENAI_API_KEY")
bearer_token = os.getenv("X_BEARER_TOKEN")
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

# Debug: Print first 10 chars of API key
logger.info(f"Using OpenAI API key starting with: {openai_api_key[:10] if openai_api_key else 'None'}")

# Validate OpenAI API key
if not openai_api_key:
    raise ValueError("OpenAI API key not found in environment variables")

# Initialize clients
try:
    openai_client = OpenAI(api_key=openai_api_key)
    logger.info("Successfully initialized OpenAI client")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {e}")
    raise

x_client = tweepy.Client(bearer_token=bearer_token)
youtube_client = None

def get_youtube_client():
    """Get or initialize the YouTube client."""
    global youtube_client
    if youtube_client is None:
        if not youtube_api_key:
            raise ValueError("YouTube API key not found in environment variables")
        try:
            youtube_client = build("youtube", "v3", developerKey=youtube_api_key)
            logger.info("Successfully initialized YouTube client")
        except Exception as e:
            logger.error(f"Error initializing YouTube client: {e}")
            raise
    return youtube_client

def get_chatgpt_recommendations(platform, categories, num_accounts=5):
    """Ask ChatGPT for top X users or YouTube channels with improved multi-category filtering."""
    platform_text = "X (Twitter) users" if platform == "X" else "YouTube channels"
    
    # Parse categories into primary and secondary
    categories = [c.strip().lower() for c in ' '.join(categories).replace(',', ' ').split()]
    primary_category = categories[0] if categories else ""
    secondary_categories = categories[1:] if len(categories) > 1 else []
    
    category_str = ', '.join(categories)
    logger.info(f"Searching for {num_accounts} {platform_text} with primary: {primary_category}, secondary: {secondary_categories}")
    
    # Adjust prompt based on whether it's a single category or multiple
    if not secondary_categories:
        prompt = (
            f"You are an expert at finding influential {platform_text} in the {primary_category} space. "
            f"Find {num_accounts} highly relevant accounts focused on {primary_category}.\n\n"
            "Focus on finding ACTIVE accounts that:\n"
            "1. Create valuable content about this topic\n"
            "2. Show genuine expertise or involvement\n"
            "3. Have real influence in the community\n"
            "4. Are currently active and engaged\n\n"
            f"For example, with 'bitcoin' look for:\n"
            "- Bitcoin developers and contributors\n"
            "- Crypto educators and analysts\n"
            "- Bitcoin-focused entrepreneurs\n"
            "- Influential community members\n\n"
            "Provide for each account:\n"
            "1. Username (exact handle, no '@')\n"
            "2. Their specific role/expertise\n"
            "3. Why they're influential (concrete examples)\n"
            "4. Follower count if known\n\n"
            "Format:\n"
            "username: [handle]\n"
            "description: [specific role]\n"
            "relevance: [concrete examples]\n"
            "followers: [count]\n\n"
            f"Find EXACTLY {num_accounts} accounts. Prioritize those with clear evidence of expertise."
        )
    else:
        prompt = (
            f"You are an expert at finding {platform_text} in the cryptocurrency and technology space. "
            f"Find {num_accounts} highly relevant accounts focused on '{primary_category}'"
            f"{' who also work with: ' + ', '.join(secondary_categories) if secondary_categories else ''}.\n\n"
            "Focus on finding SPECIFIC, ACTIVE professionals who:\n"
            "1. Have strong expertise in the primary topic\n"
            "2. Create valuable content or offer services\n"
            "3. Are likely open to collaboration/work\n"
            "4. Show genuine involvement (not just casual mentions)\n\n"
            "Examples of good matches:\n"
            "- For 'bitcoin design': Designers who work on Bitcoin projects, accept crypto, or create crypto-related designs\n"
            "- For 'bitcoin web': Web developers building Bitcoin tools or sites, accepting crypto payments\n"
            "- For 'bitcoin graphics': Visual artists creating Bitcoin content, NFT creators, crypto brand designers\n\n"
            "Provide for each account:\n"
            "1. Username (exact handle, no '@')\n"
            "2. Their specific focus/expertise\n"
            "3. Why they're relevant (concrete examples)\n"
            "4. Follower count if known\n\n"
            "Format:\n"
            "username: [handle]\n"
            "description: [specific focus]\n"
            "relevance: [concrete examples of work/involvement]\n"
            "followers: [count]\n\n"
            f"Find EXACTLY {num_accounts} accounts. Prioritize those with clear evidence of involvement over general interest."
        )
    
    try:
        logger.info(f"Making OpenAI API call for {platform} with filters: {category_str}")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at finding highly specific, relevant social media accounts. Focus on quality over quantity. Always provide concrete examples of why each account matches the criteria."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7  # Slightly higher for single terms
        )
        content = response.choices[0].message.content
        logger.info(f"OpenAI suggested accounts for '{category_str}'")
        return content
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {e}")
        raise

def parse_recommendations(chatgpt_response):
    """Parse ChatGPT's response into a list of account dictionaries."""
    accounts = []
    current_account = {}
    
    try:
        # Split response into blocks
        blocks = chatgpt_response.strip().split('\n\n')
        
        for block in blocks:
            # Skip empty blocks
            if not block.strip():
                continue
                
            lines = block.strip().split('\n')
            current_account = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Remove any numbering (e.g., "1. username: ...")
                if line[0].isdigit() and '. ' in line:
                    line = line.split('. ', 1)[1]
                
                # Parse each field
                if line.startswith('username:'):
                    username = line.split(':', 1)[1].strip().strip('@')
                    if username:  # Only add if username is not empty
                        current_account['username'] = username
                elif line.startswith('description:'):
                    current_account['description'] = line.split(':', 1)[1].strip()
                elif line.startswith('relevance:'):
                    current_account['reason'] = line.split(':', 1)[1].strip()
                elif line.startswith('followers:'):
                    follower_str = line.split(':', 1)[1].strip().lower()
                    # Convert k/m to numbers
                    if 'k' in follower_str:
                        followers = int(float(follower_str.replace('k', '')) * 1000)
                    elif 'm' in follower_str:
                        followers = int(float(follower_str.replace('m', '')) * 1000000)
                    else:
                        try:
                            followers = int(follower_str.replace(',', ''))
                        except:
                            followers = 0
                    current_account['followers_count'] = followers
            
            # Add account if it has required fields
            if 'username' in current_account:
                current_account['source'] = 'openai'
                accounts.append(current_account)
            else:
                logger.warning(f"Skipped block due to missing username: {block}")
    
    except Exception as e:
        logger.error(f"Error parsing ChatGPT response: {e}")
        logger.debug(f"Response that failed: {chatgpt_response}")
    
    logger.info(f"Successfully parsed {len(accounts)} accounts")
    return accounts

def enrich_x_data(accounts, categories=None, num_accounts=5):
    """
    Enrich account data with X profile information.
    Returns a list of enriched account data.
    """
    try:
        enriched = []
        seen_usernames = set()
        
        # First, try to get data for OpenAI suggested accounts
        for account in accounts:
            username = account.get('username', '').strip('[]@')  # Clean username
            if not username or username in seen_usernames:
                continue
                
            try:
                # Get user data from X
                user = x_client.get_user(
                    username=username,
                    user_fields=['public_metrics', 'description', 'name']
                )
                if not user.data:
                    continue
                
                # Extract metrics
                metrics = user.data.public_metrics
                
                # Create enriched account data
                enriched_account = {
                    'username': user.data.username,
                    'name': user.data.name,
                    'description': user.data.description,
                    'followers_count': metrics.get('followers_count', 0),
                    'following_count': metrics.get('following_count', 0),
                    'reason': account.get('reason', ''),
                    'source': account.get('source', 'openai')
                }
                
                enriched.append(enriched_account)
                seen_usernames.add(user.data.username)
                
                logger.debug(f"Enriched account data for {user.data.username}")
                
            except Exception as e:
                logger.warning(f"Could not get X data for {username}: {e}")
                continue
        
        # If we don't have enough accounts, try fallback search
        if len(enriched) < num_accounts and categories:
            logger.info("Not enough enriched accounts, trying fallback search")
            fallback = search_x_by_keywords(categories, num_accounts - len(enriched), seen_usernames)
            enriched.extend(fallback)
        
        # Sort by follower count and take top N
        enriched.sort(key=lambda x: x.get('followers_count', 0), reverse=True)
        return enriched[:num_accounts]
        
    except Exception as e:
        logger.error(f"Error in X data enrichment: {e}")
        return []

def search_x_by_keywords(categories, num_accounts, excluded_usernames=None):
    """
    Fallback search using X search API.
    """
    try:
        # Build search query
        search_terms = []
        for cat in categories:
            search_terms.extend([
                cat,
                f'"{cat} expert"',
                f'"{cat} dev"',
                f'"{cat} developer"',
                f'"{cat} founder"'
            ])
            
        query = f'({" OR ".join(search_terms)}) -is:retweet lang:en min_followers:1000'
        logger.info(f"Searching X with query: {query}")
        
        # Search X
        results = x_client.search_recent_tweets(
            query=query,
            max_results=100,
            tweet_fields=['author_id', 'public_metrics'],
            user_fields=['public_metrics', 'description', 'name'],
            expansions=['author_id']
        )
        
        if not results.data:
            logger.info("Fallback search found no tweets")
            return []
            
        # Get unique authors sorted by followers
        authors = {}
        for user in results.includes['users']:
            if user.username in (excluded_usernames or set()):
                continue
                
            authors[user.id] = {
                'username': user.username,
                'name': user.name,
                'description': user.description,
                'followers_count': user.public_metrics.get('followers_count', 0),
                'following_count': user.public_metrics.get('following_count', 0),
                'reason': f'Active in {categories[0]} discussions',
                'source': 'fallback'
            }
            
        # Sort by followers and return top N
        sorted_authors = sorted(
            authors.values(),
            key=lambda x: x.get('followers_count', 0),
            reverse=True
        )
        
        logger.info(f"Fallback search found {len(sorted_authors)} accounts")
        return sorted_authors[:num_accounts]
        
    except Exception as e:
        logger.error(f"Error in fallback search: {e}")
        return []

def enrich_youtube_data(accounts):
    """Fetch YouTube subscriber count and description."""
    try:
        client = get_youtube_client()
    except ValueError as e:
        logger.error(f"YouTube API error: {e}")
        return []
    
    enriched = []
    for account in accounts:
        try:
            response = client.search().list(q=account["name"], type="channel", part="id").execute()
            if not response.get("items"):
                continue
                
            channel_id = response["items"][0]["id"]["channelId"]
            details = client.channels().list(id=channel_id, part="snippet,statistics").execute()
            if not details.get("items"):
                continue
                
            item = details["items"][0]
            enriched.append({
                "username": account["name"],
                "name": item["snippet"]["title"],
                "followers_count": int(item["statistics"]["subscriberCount"]),
                "following_count": None,  # YouTube doesn't provide this
                "description": item["snippet"]["description"] or account["description"],
                "reason": account["reason"]
            })
        except Exception as e:
            logger.error(f"Error fetching YouTube data for {account['name']}: {e}")
    return enriched

def suggest_accounts(platform, categories):
    """Suggest accounts and get approval."""
    raw_response = get_chatgpt_recommendations(platform, categories)
    accounts = parse_recommendations(raw_response)
    enriched_accounts = enrich_x_data(accounts, categories) if platform == "X" else enrich_youtube_data(accounts)
    
    print(f"\nRecommended {platform} Accounts:")
    for i, acc in enumerate(enriched_accounts, 1):
        count_label = "Followers" if platform == "X" else "Subscribers"
        count = acc["followers_count"]
        print(f"{i}. {platform} Name: {acc['name']}")
        print(f"   {count_label}: {count:,}")
        print(f"   Bio: {acc['description']}")
        print(f"   Content: {acc.get('description', '')}")
        print(f"   Why Chosen: {acc['reason']}\n")
    
    approved = []
    while True:
        choice = input("Enter numbers of accounts to approve (e.g., '1 3 5') or 'done': ")
        if choice.lower() == "done":
            break
        try:
            indices = [int(i) - 1 for i in choice.split()]
            approved.extend([enriched_accounts[i] for i in indices if 0 <= i < len(enriched_accounts)])
        except (ValueError, IndexError):
            print("Invalid input. Use space-separated numbers or 'done'.")
    
    return approved

def update_target_accounts(approved_accounts, filename="target_accounts.json"):
    """Update the dynamic target_accounts list."""
    try:
        with open(filename, "r") as f:
            current_accounts = json.load(f).get("target_accounts", [])
    except FileNotFoundError:
        current_accounts = []
    
    # Remove duplicates by name while preserving order
    seen = set()
    updated_accounts = []
    for acc in current_accounts + approved_accounts:
        if acc["username"] not in seen:
            seen.add(acc["username"])
            updated_accounts.append(acc)
    
    with open(filename, "w") as f:
        json.dump({"target_accounts": updated_accounts}, f, indent=4)
    logger.info(f"Updated target_accounts.json with {len(updated_accounts)} accounts.")

def check_credentials(platform):
    """Check if required credentials are available."""
    if platform == "X":
        if not bearer_token:
            logger.error("Error: X_BEARER_TOKEN not found in environment variables")
            print("Please set up your X API credentials in the .env file:")
            print("X_BEARER_TOKEN=your_bearer_token")
            return False
    else:  # YouTube
        if not youtube_api_key:
            logger.error("Error: YOUTUBE_API_KEY not found in environment variables")
            print("Please set up your YouTube API credentials in the .env file:")
            print("YOUTUBE_API_KEY=your_api_key")
            return False
    
    if not openai_api_key:
        logger.error("Error: OPENAI_API_KEY not found in environment variables")
        print("Please set up your OpenAI API key in the .env file:")
        print("OPENAI_API_KEY=your_api_key")
        return False
    
    return True

def find_accounts(categories, num_accounts=5):
    """Find relevant social media accounts based on categories."""
    logger.info(f"Finding accounts for categories: {categories}")
    
    try:
        # Step 1: Get recommendations from OpenAI
        recommendations = get_chatgpt_recommendations('X', categories, num_accounts)
        
        # Step 2: Parse recommendations
        accounts = parse_recommendations(recommendations)
        if not accounts:
            logger.warning("No accounts found from OpenAI recommendations")
            return []
            
        # Step 3: Enrich with X data
        enriched = enrich_x_data(accounts, categories=categories, num_accounts=num_accounts)
        if not enriched:
            logger.warning("No accounts found after enrichment")
            return []
            
        logger.info(f"Found {len(enriched)} accounts")
        return enriched
        
    except Exception as e:
        logger.error(f"Error finding accounts: {e}")
        return []

def run_user_recommender():
    """Main function to run the user recommender with improved multi-category filtering."""
    print("\nX/YouTube Account Recommender")
    print("----------------------------")
    platform = input("Choose platform (X or YouTube): ").strip().capitalize()
    if platform not in ["X", "YouTube"]:
        logger.error("Invalid platform. Use 'X' or 'YouTube'.")
        print("Invalid platform. Use 'X' or 'YouTube'.")
        return
    
    if not check_credentials(platform):
        return
    
    print("\nEnter up to 5 categories/filters separated by spaces.")
    print("Examples:")
    print("- 'bitcoin graphic design ui'")
    print("- 'ballet technique france'")
    print("- 'soccer fitness youth'")
    categories = input(f"\nEnter filters for {platform}: ").strip().split()
    
    if not categories:
        logger.error("No categories provided.")
        print("No categories provided.")
        return
    
    if len(categories) > 5:
        logger.warning("Too many categories provided. Using first 5 for best results.")
        print("\nNote: Using first 5 categories for best results.")
        categories = categories[:5]
    
    try:
        print(f"\nSearching for {platform} accounts matching filters: {', '.join(categories)}...")
        approved_accounts = suggest_accounts(platform, categories)
        
        if approved_accounts:
            update_target_accounts(approved_accounts)
            print(f"\nSaved {len(approved_accounts)} accounts to target_accounts.json")
            
            if input("\nWant to refine your search? (y/n): ").lower() == 'y':
                run_user_recommender()
        else:
            print("\nNo accounts were approved. Try different filters?")
            if input("Want to try again? (y/n): ").lower() == 'y':
                run_user_recommender()
                
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        print("Please check your API credentials and try again.")

if __name__ == "__main__":
    run_user_recommender()

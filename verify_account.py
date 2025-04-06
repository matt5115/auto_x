import tweepy
from dotenv import load_dotenv
import os

load_dotenv()

# Set up authentication with API v2
client = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
)

# Get and print authenticated user's information
try:
    me = client.get_me()
    print("\nAuthenticated Account Information:")
    print(f"Username: @{me.data.username}")
    print(f"Display Name: {me.data.name}")
    print(f"Account ID: {me.data.id}")
    
    # Test post capability (without actually posting)
    print("\nChecking post capability...")
    if client.get_oauth1_user_auth():
        print("✓ Account has posting capability")
    else:
        print("✗ Account does not have posting capability")
        
except Exception as e:
    print(f"Error verifying credentials: {str(e)}")

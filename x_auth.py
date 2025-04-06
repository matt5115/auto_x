from requests_oauthlib import OAuth1Session
import os
from dotenv import load_dotenv
from models import User
import json

load_dotenv()

X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_CALLBACK_URL = os.getenv('X_CALLBACK_URL', 'http://127.0.0.1:5002/callback')

def get_request_token():
    oauth = OAuth1Session(
        X_API_KEY,
        client_secret=X_API_SECRET,
        callback_uri=X_CALLBACK_URL
    )
    
    try:
        resp = oauth.fetch_request_token('https://api.twitter.com/oauth/request_token')
        return resp.get('oauth_token'), resp.get('oauth_token_secret')
    except Exception as e:
        print(f"Error getting request token: {str(e)}")
        return None, None

def get_authorization_url(request_token):
    return f'https://api.twitter.com/oauth/authorize?oauth_token={request_token}'

def get_access_token(request_token, request_token_secret, oauth_verifier):
    oauth = OAuth1Session(
        X_API_KEY,
        client_secret=X_API_SECRET,
        resource_owner_key=request_token,
        resource_owner_secret=request_token_secret,
        verifier=oauth_verifier
    )
    
    try:
        resp = oauth.fetch_access_token('https://api.twitter.com/oauth/access_token')
        return resp.get('oauth_token'), resp.get('oauth_token_secret'), resp.get('screen_name')
    except Exception as e:
        print(f"Error getting access token: {str(e)}")
        return None, None, None

def verify_credentials(access_token, access_token_secret):
    oauth = OAuth1Session(
        X_API_KEY,
        client_secret=X_API_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret
    )
    
    try:
        resp = oauth.get('https://api.twitter.com/2/users/me')
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        print(f"Error verifying credentials: {str(e)}")
        return None

def post_tweet(user, text):
    if not user.x_token or not user.x_token_secret:
        return False, "User not authenticated with X"
    
    oauth = OAuth1Session(
        X_API_KEY,
        client_secret=X_API_SECRET,
        resource_owner_key=user.x_token,
        resource_owner_secret=user.x_token_secret
    )
    
    try:
        resp = oauth.post(
            'https://api.twitter.com/2/tweets',
            json={'text': text}
        )
        if resp.status_code == 201:
            return True, resp.json()
        return False, f"Error posting tweet: {resp.text}"
    except Exception as e:
        return False, f"Error posting tweet: {str(e)}"

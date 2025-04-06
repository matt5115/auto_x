from flask import Flask, request, redirect, url_for
from requests_oauthlib import OAuth1Session
import os
from dotenv import load_dotenv
import webbrowser
import json

load_dotenv()

app = Flask(__name__)

# X API credentials
X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
CALLBACK_URL = 'http://127.0.0.1:5000/callback'

# Store OAuth tokens temporarily
oauth_tokens = {}

@app.route('/')
def home():
    # Step 1: Get request token
    oauth = OAuth1Session(
        X_API_KEY,
        client_secret=X_API_SECRET,
        callback_uri=CALLBACK_URL
    )
    
    try:
        resp = oauth.fetch_request_token('https://api.twitter.com/oauth/request_token')
        oauth_tokens['request_token'] = resp.get('oauth_token')
        oauth_tokens['request_token_secret'] = resp.get('oauth_token_secret')
        
        # Step 2: Redirect user to X for authentication
        authorization_url = oauth.authorization_url('https://api.twitter.com/oauth/authorize')
        return f'''
        <h1>X Account Authentication</h1>
        <p>Click the button below to authenticate your X account:</p>
        <a href="{authorization_url}" style="
            display: inline-block;
            background-color: #1DA1F2;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            font-family: Arial, sans-serif;
        ">Authenticate with X</a>
        '''
    except Exception as e:
        return f'<h1>Error</h1><p>Failed to get request token: {str(e)}</p>'

@app.route('/callback')
def callback():
    # Step 3: Get access token
    verifier = request.args.get('oauth_verifier')
    oauth = OAuth1Session(
        X_API_KEY,
        client_secret=X_API_SECRET,
        resource_owner_key=oauth_tokens.get('request_token'),
        resource_owner_secret=oauth_tokens.get('request_token_secret'),
        verifier=verifier
    )
    
    try:
        resp = oauth.fetch_access_token('https://api.twitter.com/oauth/access_token')
        
        # Get the access tokens
        access_token = resp.get('oauth_token')
        access_token_secret = resp.get('oauth_token_secret')
        screen_name = resp.get('screen_name')
        
        # Update .env file with new tokens
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        with open(env_path, 'r') as file:
            lines = file.readlines()
        
        new_lines = []
        for line in lines:
            if line.startswith('X_ACCESS_TOKEN='):
                new_lines.append(f'X_ACCESS_TOKEN={access_token}\n')
            elif line.startswith('X_ACCESS_TOKEN_SECRET='):
                new_lines.append(f'X_ACCESS_TOKEN_SECRET={access_token_secret}\n')
            else:
                new_lines.append(line)
        
        with open(env_path, 'w') as file:
            file.writelines(new_lines)
        
        return f'''
        <h1>Authentication Successful!</h1>
        <p>Your X account @{screen_name} has been successfully authenticated.</p>
        <p>The access tokens have been updated in your .env file.</p>
        <p>You can now close this window and return to your terminal.</p>
        '''
    except Exception as e:
        return f'<h1>Error</h1><p>Failed to get access token: {str(e)}</p>'

if __name__ == '__main__':
    print("\nStarting X authentication process...")
    print("A browser window will open. Please follow the instructions there.")
    webbrowser.open('http://127.0.0.1:5000/')
    app.run(port=5000)

"""Application configuration settings."""

# Feature flags
ENABLE_TWITTER_AUTH = True  # Set to True to re-enable Twitter OAuth login

# Twitter API configuration
TWITTER_API_VERSION = "2.0"  # Use Twitter API v2
TWITTER_CALLBACK_URL = "http://127.0.0.1:5000/callback"

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twitter API Configuration
TWITTER_CLIENT_ID = os.getenv('TWITTER_CLIENT_ID')
TWITTER_CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET')
TWITTER_REDIRECT_URI = os.getenv('TWITTER_REDIRECT_URI')
TWITTER_SCOPES = 'tweet.read tweet.write users.read offline.access'

# Twitter API URLs
TWITTER_AUTHORIZATION_URL = 'https://twitter.com/i/oauth2/authorize'
TWITTER_TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'
TWITTER_TWEET_URL = 'https://api.twitter.com/2/tweets'
TWITTER_SEARCH_URL = 'https://api.twitter.com/2/tweets/search/recent'

# Token storage
TOKEN_FILE = 'tokens.json'

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
SITE_URL = os.getenv('SITE_URL')
SITE_NAME = os.getenv('SITE_NAME')


# Bot Configuration
TARGET_USERNAME = os.getenv('TARGET_USERNAME')
TARGET_TWEET_IDS_FILE = 'target_tweet_ids.txt'
POLLING_INTERVAL_SECONDS = 60  # 10 minutes
SEARCH_WINDOW_MINUTES = 2
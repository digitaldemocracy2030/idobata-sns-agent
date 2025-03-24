import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twitter API Configuration
TWITTER_CLIENT_ID = os.getenv('TWITTER_CLIENT_ID')
TWITTER_CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET')
TWITTER_REDIRECT_URI = os.getenv('TWITTER_REDIRECT_URI')
TWITTER_SCOPES = os.getenv('TWITTER_SCOPES')

# Twitter API URLs
TWITTER_AUTHORIZATION_URL = os.getenv('TWITTER_AUTHORIZATION_URL')
TWITTER_TOKEN_URL = os.getenv('TWITTER_TOKEN_URL')
TWITTER_TWEET_URL = os.getenv('TWITTER_TWEET_URL')
TWITTER_SEARCH_URL = os.getenv('TWITTER_SEARCH_URL')

# Token storage
TOKEN_FILE = os.getenv('TOKEN_FILE')

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
SITE_URL = os.getenv('SITE_URL')
SITE_NAME = os.getenv('SITE_NAME')

# Delib API Configuration
DELIB_API_BASE_URL = os.getenv('DELIB_API_BASE_URL', 'http://delib.takahiroanno.com/backend/api')
DELIB_ADMIN_API_KEY = os.getenv('DELIB_ADMIN_API_KEY')
DEFAULT_PROJECT_ID = os.getenv('DEFAULT_PROJECT_ID')
DELIB_ANALYTICS_URL = os.getenv('DELIB_ANALYTICS_URL', 'https://delib.takahiroanno.com/projects/{project_id}/analytics?question=')

# Bot Configuration
TARGET_USERNAME = os.getenv('TARGET_USERNAME')
TARGET_TWEET_IDS_FILE = os.getenv('TARGET_TWEET_IDS_FILE')
POLLING_INTERVAL_SECONDS = int(os.getenv('POLLING_INTERVAL_SECONDS', 60))
SEARCH_WINDOW_MINUTES = int(os.getenv('SEARCH_WINDOW_MINUTES', 5))
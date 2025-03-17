# Twitter Bot with OpenAI Integration

This bot monitors Twitter for mentions or replies to specific tweets and automatically responds using OpenAI's GPT model.

## Features

- OAuth 2.0 authentication with Twitter API
- Automatic token refresh
- Monitoring for mentions and replies to specific tweets
- AI-powered responses using OpenAI's GPT model
- Environment variable configuration

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   cp .env.example .env
   ```
4. Edit the `.env` file with your:
   - Twitter API credentials (Client ID, Client Secret, Redirect URI)
   - OpenAI API key
   - Target username to monitor

## Twitter API Setup

1. Create a Twitter Developer account at https://developer.twitter.com/
2. Create a project and app
3. Configure your app with OAuth 2.0 and the following permissions:
   - Read and Write permissions
   - Type of App: Web App, Automated App or Bot
4. Set your Redirect URI (e.g., https://localhost:3000/callback)
5. Copy your Client ID and Client Secret to the `.env` file

## Usage

1. (Optional) Edit `target_tweet_ids.txt` to add specific tweet IDs you want to monitor for replies
2. Run the bot:
   ```
   python main.py
   ```
3. On first run, you'll be prompted to authenticate with Twitter:
   - Open the provided URL in your browser
   - Authorize the application
   - Copy the redirected URL and paste it back into the terminal

The bot will now continuously monitor Twitter and respond to mentions and replies.

## Configuration

- `TARGET_USERNAME`: Twitter username to monitor for mentions (without @)
- `target_tweet_ids.txt`: List of tweet IDs to monitor for replies (one per line)
- `POLLING_INTERVAL_SECONDS`: How often to check for new tweets (default: 600 seconds / 10 minutes)
- `SEARCH_WINDOW_MINUTES`: How far back to search for tweets (default: 10 minutes)

## Files

- `main.py`: Entry point for the application
- `config.py`: Configuration loading from environment variables
- `twitter/`: Twitter API integration
  - `auth.py`: Authentication with Twitter API
  - `api.py`: Twitter API operations
- `openai_client/`: OpenAI integration
  - `api.py`: OpenAI API operations
- `utils/`: Utility functions
  - `file_utils.py`: File operations

## License

See the LICENSE file for details.
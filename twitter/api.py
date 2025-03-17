import requests
from datetime import datetime, timedelta

from config import (
    TWITTER_TWEET_URL,
    TWITTER_SEARCH_URL,
    SEARCH_WINDOW_MINUTES
)


def build_search_query(username, tweet_ids):
    """
    Build a search query for Twitter API.
    
    Example:
     - username = "YourAccount"  # Account name (without @)
     - tweet_ids = ["1234567890", "9876543210"]
    Returns: "to:YourAccount OR in_reply_to_tweet_id:1234567890 OR in_reply_to_tweet_id:9876543210"
    """
    query_parts = []
    if username:
        query_parts.append(f"to:{username}")
    for tid in tweet_ids:
        query_parts.append(f"in_reply_to_tweet_id:{tid}")
    if not query_parts:
        return ""  # Return empty if no criteria specified
    return " OR ".join(query_parts)


def fetch_recent_tweets(access_token, query, minutes=SEARCH_WINDOW_MINUTES):
    """
    Fetch tweets created in the last 'minutes' that match the query.
    
    Args:
        access_token: Twitter API access token
        query: Search query string
        minutes: How far back to search (default: from config)
        
    Returns:
        List of tweet objects
    """
    if not query:
        return []

    # Calculate start time in ISO8601 format
    start_time = (datetime.utcnow() - timedelta(minutes=minutes)).replace(microsecond=0).isoformat() + "Z"

    params = {
        "query": query,
        "start_time": start_time,
        "max_results": 10,  # Adjust as needed
        "expansions": "author_id",
        "tweet.fields": "conversation_id,in_reply_to_user_id,created_at",
        "user.fields": "username"
    }
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    resp = requests.get(TWITTER_SEARCH_URL, params=params, headers=headers)
    if resp.status_code != 200:
        print(f"Error fetching tweets: {resp.status_code} {resp.text}")
        return []

    data = resp.json()
    return data.get("data", [])  # Return list of tweet objects


def fetch_conversation_history(access_token, tweet_id, max_tweets=5, tweet_author_id=None):
    """
    Fetch conversation history for a given tweet (up to max_tweets previous tweets).
    Only includes tweets from the tweet author, original poster, or TARGET_USERNAME.
    
    Args:
        access_token: Twitter API access token
        tweet_id: ID of the tweet to get conversation history for
        max_tweets: Maximum number of previous tweets to fetch
        tweet_author_id: ID of the author of the tweet (optional)
        
    Returns:
        List of tweet objects in chronological order (oldest first)
    """
    # First, get the conversation_id for this tweet
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    # Get the current tweet to find its conversation_id
    resp = requests.get(
        f"{TWITTER_TWEET_URL}/{tweet_id}",
        params={"tweet.fields": "conversation_id,created_at"},
        headers=headers
    )
    
    if resp.status_code != 200:
        print(f"Error fetching tweet: {resp.status_code} {resp.text}")
        return []
    
    tweet_data = resp.json().get("data", {})
    conversation_id = tweet_data.get("conversation_id")
    
    # Use the provided tweet_author_id if available
    current_author_id = tweet_author_id
    current_author_username = None
    
    if not conversation_id:
        print(f"Could not find conversation_id for tweet {tweet_id}")
        return []
    
    # Get the original tweet in the conversation to find the original author
    # This is needed to filter tweets by the original poster
    params = {
        "query": f"conversation_id:{conversation_id}",
        "max_results": 10,
        "tweet.fields": "author_id,created_at",
        "user.fields": "username",
        "expansions": "author_id"
    }
    
    resp = requests.get(TWITTER_SEARCH_URL, params=params, headers=headers)
    
    if resp.status_code != 200:
        print(f"Error fetching conversation: {resp.status_code} {resp.text}")
        return []
    
    data = resp.json()
    all_tweets = data.get("data", [])
    
    # Get user information
    users = {}
    original_author_id = None
    original_author_username = None
    
    if "includes" in data and "users" in data["includes"]:
        for user in data["includes"]["users"]:
            users[user["id"]] = user["username"]
            # If this user is the author of the current tweet, store their username
            if user["id"] == current_author_id:
                current_author_username = user["username"]
                print(f"Current tweet author: @{current_author_username}")
    
    # Find the original tweet (oldest in the conversation)
    if all_tweets:
        # Sort by created_at to find the oldest tweet
        all_tweets.sort(key=lambda x: x.get("created_at", ""))
        original_author_id = all_tweets[0].get("author_id")
        original_author_username = users.get(original_author_id, "Unknown")
        
        print(f"Original author of the conversation: @{original_author_username}")
    
    # Now fetch tweets in this conversation, but only from the original author or TARGET_USERNAME
    from config import TARGET_USERNAME
    
    # Build a query that filters by conversation_id AND (current tweet author OR original author OR TARGET_USERNAME)
    author_filter = ""
    
    # Add current tweet author to filter
    if current_author_username:
        author_filter = f"from:{current_author_username}"
    
    # Add original conversation author to filter if different from current author
    if original_author_username and original_author_username != current_author_username:
        if author_filter:
            author_filter += f" OR from:{original_author_username}"
        else:
            author_filter = f"from:{original_author_username}"
    
    # if TARGET_USERNAME:
    #     if author_filter:
    #         author_filter += f" OR from:{TARGET_USERNAME}"
    #     else:
    #         author_filter = f"from:{TARGET_USERNAME}"
    
    # Final query combines conversation_id with author filter
    query = f"conversation_id:{conversation_id}"
    if author_filter:
        query += f" ({author_filter})"
    
    print(f"Using filtered query: {query}")
    
    params = {
        "query": query,
        "max_results": 10,  # Twitter API requires min 10
        "tweet.fields": "author_id,created_at,in_reply_to_user_id,referenced_tweets",
        "user.fields": "username",
        "expansions": "author_id"
    }
    
    resp = requests.get(TWITTER_SEARCH_URL, params=params, headers=headers)
    
    if resp.status_code != 200:
        print(f"Error fetching filtered conversation: {resp.status_code} {resp.text}")
        return []
    
    data = resp.json()
    tweets = data.get("data", [])
    
    # Update user information
    if "includes" in data and "users" in data["includes"]:
        for user in data["includes"]["users"]:
            users[user["id"]] = user["username"]
    
    # Format tweets with username
    formatted_tweets = []
    for tweet in tweets:
        author_id = tweet.get("author_id")
        username = users.get(author_id, "Unknown")
        
        formatted_tweets.append({
            "id": tweet["id"],
            "username": username,
            "text": tweet["text"],
            "created_at": tweet.get("created_at")
        })
    
    # Sort by created_at (oldest first)
    formatted_tweets.sort(key=lambda x: x.get("created_at", ""))
    
    # Remove the current tweet if it's in the list
    formatted_tweets = [t for t in formatted_tweets if t["id"] != tweet_id]
    
    # Return up to max_tweets (most recent tweets first)
    if len(formatted_tweets) > max_tweets:
        print(f"Limiting conversation history from {len(formatted_tweets)} to {max_tweets} tweets")
        return formatted_tweets[-max_tweets:]
    
    return formatted_tweets


def reply_to_tweet(access_token, tweet_id, reply_text):
    """
    Post a reply to a specific tweet.
    
    Args:
        access_token: Twitter API access token
        tweet_id: ID of the tweet to reply to
        reply_text: Text content of the reply
        
    Returns:
        True if successful, False otherwise
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "text": reply_text,
        "reply": {
            "in_reply_to_tweet_id": tweet_id
        }
    }
    resp = requests.post(TWITTER_TWEET_URL, json=payload, headers=headers)
    if resp.status_code != 201:
        print(f"Error posting reply: {resp.status_code} {resp.text}")
        return False
    else:
        print(f"Reply posted successfully (tweet_id={tweet_id}).")
        return True
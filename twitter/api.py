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


def fetch_conversation_history(access_token, tweet_id, max_tweets=5):
    """
    Fetch the direct parent tweets (thread lineage) for a given tweet.
    This returns only the direct parent, grandparent, etc. tweets in the thread,
    not all replies in the conversation.
    
    Args:
        access_token: Twitter API access token
        tweet_id: ID of the tweet to get thread lineage for
        max_tweets: Maximum number of parent tweets to fetch
        
    Returns:
        List of tweet objects in chronological order (oldest first)
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Dictionary to store all tweets we fetch
    tweets_by_id = {}
    # Dictionary to store user information
    users = {}
    # List to track the thread lineage
    thread_lineage = []
    # Current tweet ID we're processing
    current_id = tweet_id
    # Counter to limit the number of API calls
    count = 0
    
    # Continue until we reach max_tweets or can't find any more parent tweets
    while current_id and count < max_tweets:
        # Get the current tweet with referenced_tweets expansion
        resp = requests.get(
            f"{TWITTER_TWEET_URL}/{current_id}",
            params={
                "tweet.fields": "created_at,referenced_tweets",
                "expansions": "author_id,referenced_tweets.id,referenced_tweets.id.author_id",
                "user.fields": "username"
            },
            headers=headers
        )
        
        if resp.status_code != 200:
            print(f"Error fetching tweet {current_id}: {resp.status_code} {resp.text}")
            break
        
        data = resp.json()
        
        # Store the current tweet
        if "data" in data:
            tweet = data["data"]
            tweets_by_id[tweet["id"]] = tweet
            
            # If this isn't the original tweet we're looking for history for, add it to our lineage
            if tweet["id"] != tweet_id:
                thread_lineage.append(tweet)
        
        # Store user information
        if "includes" in data and "users" in data["includes"]:
            for user in data["includes"]["users"]:
                users[user["id"]] = user["username"]
        
        # Store any referenced tweets
        if "includes" in data and "tweets" in data["includes"]:
            for ref_tweet in data["includes"]["tweets"]:
                tweets_by_id[ref_tweet["id"]] = ref_tweet
        
        # Find the parent tweet ID (the tweet this one is replying to)
        parent_id = None
        if "data" in data and "referenced_tweets" in data["data"]:
            for ref in data["data"]["referenced_tweets"]:
                if ref["type"] == "replied_to":
                    parent_id = ref["id"]
                    break
        
        # Move to the parent tweet for the next iteration
        current_id = parent_id
        count += 1
    
    # Format the tweets with username information
    formatted_tweets = []
    for tweet in thread_lineage:
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
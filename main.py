#!/usr/bin/env python3
import time
from config import (
    TARGET_USERNAME,
    POLLING_INTERVAL_SECONDS
)
from twitter.auth import get_valid_token
from twitter.api import build_search_query, fetch_recent_tweets, reply_to_tweet, fetch_conversation_history
from typing import Optional
from chat_client.api import generate_reply
from utils.file_utils import (
    read_target_tweet_ids,
    create_empty_target_file_if_not_exists,
    create_replied_tweets_file_if_not_exists,
    read_replied_tweet_ids,
    add_replied_tweet_id
)

# Twitter's character limit for tweets
TWITTER_CHAR_LIMIT = 280

def truncate_reply_if_needed(reply_text: Optional[str]) -> Optional[str]:
    """
    Truncate the reply text if it exceeds Twitter's character limit.
    
    Args:
        reply_text: The text to check and potentially truncate
        
    Returns:
        Truncated text if needed, or the original text if within limits
    """
    if reply_text is None:
        return None
        
    if len(reply_text) <= TWITTER_CHAR_LIMIT:
        return reply_text
    
    # Truncate the text and add an ellipsis
    truncated_text = reply_text[:TWITTER_CHAR_LIMIT - 3] + "..."
    print(f"Reply truncated from {len(reply_text)} to {len(truncated_text)} characters")
    return truncated_text


def main():
    """
    Main function that runs the Twitter bot.
    
    This function:
    1. Ensures the target tweet IDs file exists
    2. Ensures the replied tweets log file exists
    3. Gets a valid Twitter access token
    4. Continuously polls for new tweets and replies to them
    """
    print("Twitter Bot starting...")
    
    # Create target tweet IDs file if it doesn't exist
    create_empty_target_file_if_not_exists()
    
    # Create replied tweets log file if it doesn't exist
    create_replied_tweets_file_if_not_exists()
    
    # Main loop - runs continuously
    while True:
        try:
            # Get or refresh access token
            access_token = get_valid_token()

            # Read target tweet IDs from file
            tweet_ids = read_target_tweet_ids()
            
            # Read replied tweet IDs from file
            replied_tweet_ids = read_replied_tweet_ids()
            print(f"Loaded {len(replied_tweet_ids)} previously replied tweet IDs")

            # Build search query
            query = build_search_query(TARGET_USERNAME, tweet_ids)
            if not query:
                print("検索クエリが空です。TARGET_USERNAME または target_tweet_ids.txt を設定してください。")
                time.sleep(POLLING_INTERVAL_SECONDS)
                continue

            # Fetch recent tweets that match our criteria
            recent_tweets = fetch_recent_tweets(access_token, query)

            # Process each tweet
            for tweet in recent_tweets:
                tweet_id = tweet["id"]
                user_text = tweet["text"]

                print(f"[INFO] tweet_id={tweet_id}, text={user_text}")
                
                # Skip if we've already replied to this tweet
                if tweet_id in replied_tweet_ids:
                    print(f"Skipping tweet_id={tweet_id} - already replied")
                    continue
                
                # Fetch conversation history (up to 10 previous tweets)
                try:
                    # Get the author_id from the tweet
                    author_id = tweet.get("author_id")
                    conversation_history = fetch_conversation_history(access_token, tweet_id, max_tweets=10)
                    
                    if conversation_history:
                        print(f"Found {len(conversation_history)} previous tweets in the conversation")
                        for i, t in enumerate(conversation_history):
                            print(f"  [{i+1}] @{t['username']}: {t['text']}")
                    else:
                        print("No conversation history found")
                except Exception as e:
                    print(f"Error fetching conversation history: {e}")
                    conversation_history = []

                # Generate reply using local chat API with conversation history
                reply_text = generate_reply(user_text, conversation_history)

                # Only post reply if we got a valid response (not None)
                if reply_text is not None:
                    # Truncate reply if it exceeds Twitter's character limit
                    truncated_reply = truncate_reply_if_needed(reply_text)
                    
                    # Post reply to Twitter
                    reply_success = reply_to_tweet(access_token, tweet_id, truncated_reply)
                    print(f"Replying to tweet_id={tweet_id}, text={truncated_reply}")
                    
                    # If reply was successful, add to replied tweets log
                    if reply_success:
                        add_replied_tweet_id(tweet_id)
                        replied_tweet_ids.add(tweet_id)  # Add to in-memory set too
                        print(f"Added tweet_id={tweet_id} to replied tweets log")
                else:
                    print(f"Skipping reply to tweet_id={tweet_id} due to API error")

        except Exception as e:
            print(f"Error in main loop: {e}")

        # Sleep before next polling cycle
        print(f"{POLLING_INTERVAL_SECONDS // 60}分スリープします...")
        time.sleep(POLLING_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
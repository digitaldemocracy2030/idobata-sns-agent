#!/usr/bin/env python3
import time
import re
from config import (
    TARGET_USERNAME,
    POLLING_INTERVAL_SECONDS,
    DEFAULT_PROJECT_ID
)
from twitter.auth import get_valid_token
from twitter.api import build_search_query, fetch_recent_tweets, reply_to_tweet, fetch_conversation_history
from typing import Optional
from utils.file_utils import (
    read_target_tweet_ids,
    create_empty_target_file_if_not_exists,
    create_replied_tweets_file_if_not_exists,
    read_replied_tweet_ids,
    add_replied_tweet_id
)
from llm.api import generate_reply

# Twitter's character limit for tweets
TWITTER_CHAR_LIMIT = 280

def remove_mention_prefix(reply_text: Optional[str]) -> Optional[str]:
    """
    Remove Twitter-style mentions (like "@username") from the beginning of reply text.
    
    Args:
        reply_text: The text to process
        
    Returns:
        Text with leading mentions removed, or the original text if no mentions found
    """
    if reply_text is None:
        return None
    
    # Regex pattern to match "@username" at the beginning of text
    pattern = r"^\s*@\w+\s+"
    
    # Remove the mention if found
    cleaned_text = re.sub(pattern, "", reply_text)
    
    if cleaned_text != reply_text:
        print(f"Removed mention prefix from reply")
    
    return cleaned_text


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
                
                # Fetch conversation history
                try:
                    # Get the author_id from the tweet
                    author_id = tweet.get("author_id")
                    conversation_history = fetch_conversation_history(access_token, tweet_id, max_tweets=5)
                    
                    if conversation_history:
                        print(f"Found {len(conversation_history)} previous tweets in the conversation")
                        for i, t in enumerate(conversation_history):
                            print(f"  [{i+1}] @{t['username']}: {t['text']}")
                    else:
                        print("No conversation history found")
                except Exception as e:
                    print(f"Error fetching conversation history: {e}")
                    conversation_history = []

                # Generate reply using Delib API with conversation history
                reply_text = generate_reply(user_text, conversation_history, DEFAULT_PROJECT_ID)

                # Only post reply if we got a valid response (not None)
                if reply_text is not None:
                    # Remove any Twitter-style mentions from the beginning of the reply
                    cleaned_reply = remove_mention_prefix(reply_text)
                    
                    # Truncate reply if it exceeds Twitter's character limit
                    truncated_reply = truncate_reply_if_needed(cleaned_reply)
                    
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
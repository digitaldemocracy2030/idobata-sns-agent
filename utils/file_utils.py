import os
from config import TARGET_TWEET_IDS_FILE

# File to store IDs of tweets that have already been replied to
REPLIED_TWEETS_FILE = "replied_tweets.txt"


def read_target_tweet_ids(filename=TARGET_TWEET_IDS_FILE):
    """
    Read tweet IDs from a file (one ID per line).
    
    Args:
        filename: Path to the file containing tweet IDs
        
    Returns:
        List of tweet IDs, or empty list if file doesn't exist
    """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        return lines
    return []


def create_empty_target_file_if_not_exists(filename=TARGET_TWEET_IDS_FILE):
    """
    Create an empty target tweet IDs file with instructions if it doesn't exist.
    
    Args:
        filename: Path to the file to create
    """
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# このファイルには監視対象のツイートIDを1行に1つずつ記載してください\n")
            f.write("# 例:\n")
            f.write("# 1234567890123456789\n")
            f.write("# 9876543210987654321\n")
        print(f"Created empty {filename} file")


def create_replied_tweets_file_if_not_exists():
    """
    Create the replied tweets log file if it doesn't exist.
    """
    if not os.path.exists(REPLIED_TWEETS_FILE):
        with open(REPLIED_TWEETS_FILE, "w", encoding="utf-8") as f:
            f.write("# このファイルには既に返信したツイートIDが自動的に記録されます\n")
            f.write("# 手動で編集しないでください\n")
        print(f"Created empty {REPLIED_TWEETS_FILE} file")


def read_replied_tweet_ids():
    """
    Read the IDs of tweets that have already been replied to.
    
    Returns:
        Set of tweet IDs that have been replied to
    """
    if os.path.exists(REPLIED_TWEETS_FILE):
        with open(REPLIED_TWEETS_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        return set(lines)
    return set()


def add_replied_tweet_id(tweet_id):
    """
    Add a tweet ID to the replied tweets log.
    
    Args:
        tweet_id: ID of the tweet that was replied to
    """
    # Make sure the file exists
    create_replied_tweets_file_if_not_exists()
    
    # Add the tweet ID to the file
    with open(REPLIED_TWEETS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{tweet_id}\n")
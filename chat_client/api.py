import requests
import datetime
import re
from typing import List, Dict, Optional
from config import TARGET_USERNAME
API_ENDPOINT = "https://delib.takahiroanno.com/chat/api/chat"

def remove_mention_prefix(text: str) -> str:
    """
    Remove Twitter-style mentions (@username) from the beginning of text.
    
    Args:
        text: The text to process
        
    Returns:
        Text with mentions removed from the beginning
    """
    # Pattern matches @ followed by non-whitespace characters and optional whitespace
    return re.sub(r'^@\S+\s*', '', text)


def generate_reply(user_text: str, conversation_history: Optional[List[Dict]] = None) -> Optional[str]:
    """
    Generate a reply to the user's text using the local chat API.
    
    Args:
        user_text: The text to respond to
        conversation_history: Optional list of previous tweets in the conversation
        
    Returns:
        Generated reply text
    """
    try:
        # Prepare the request payload
        payload = {
            "projectId": "67d76376c29091a5f2fb8aa4",  # プロジェクトの固有ID
            "newComment": user_text,           # 新しいユーザーコメント
        }
        
        # Add conversation history if available
        if conversation_history and len(conversation_history) > 0:
            past_logs = []
            
            for tweet in conversation_history:
                # Get tweet text and remove any @mentions from the beginning
                tweet_text = tweet.get("text", "")
                cleaned_text = remove_mention_prefix(tweet_text)
                
                past_logs.append({
                    "id": tweet.get("id", ""),
                    "content": cleaned_text,
                    "timestamp": tweet.get("created_at", datetime.datetime.now().isoformat()),
                    "sender": "bot" if tweet.get("username") == TARGET_USERNAME else "user"
                })
            
            payload["pastLogs"] = past_logs
        
        # Make the API request
        response = requests.post(API_ENDPOINT, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            return result.get("response")
        else:
            error_data = response.json()
            print(f"Chat APIエラー: {error_data.get('error')} - {error_data.get('message')}")
            return None
            
    except Exception as e:
        print("Chat APIエラー:", e)
        return None
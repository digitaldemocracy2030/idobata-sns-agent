#!/usr/bin/env python3
import requests
import json
from typing import List, Dict, Optional, Any
import re
from openai import OpenAI
from config import OPENROUTER_API_KEY, DELIB_API_BASE_URL, DELIB_ADMIN_API_KEY, TARGET_USERNAME, DELIB_ANALYTICS_URL, DEFAULT_PROJECT_ID

# Initialize OpenAI client with OpenRouter base URL
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Default model to use
DEFAULT_MODEL = "google/gemini-2.0-flash-001"

# Headers for Delib API requests
DELIB_HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": DELIB_ADMIN_API_KEY
}

def convert_question_urls(text: str) -> str:
    """
    Convert question:// URLs to full analytics URLs.
    
    Args:
        text: The text containing question:// URLs
        
    Returns:
        The text with question:// URLs converted to full analytics URLs
    """
    # Pattern to match question://UUID format
    pattern = r'question://([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    
    # Replace with the analytics URL
    return re.sub(pattern, lambda m: DELIB_ANALYTICS_URL + m.group(1), text)

def add_comment_to_delib(project_id: str, user_text: str, conversation_history: List[Dict] = None) -> Dict:
    """
    Add a comment to the Delib API and return the response.
    
    Args:
        project_id: The ID of the project in the Delib API
        user_text: The text of the comment to add
        conversation_history: List of previous tweets in the conversation
        
    Returns:
        The response from the Delib API
    """
    # Format conversation context if available
    context = ""
    if conversation_history:
        context = "Previous conversation:\n"
        for tweet in conversation_history:
            username = tweet.get("username", "Unknown")
            text = tweet.get("text", "")
            context += f"{username}: {text}\n"
        
        # Add context to the comment
        full_content = f"{context}\n\nUser's new message: {user_text}"
    else:
        full_content = user_text
    
    # Prepare the request payload
    payload = {
        "content": full_content,
        "sourceType": "x",
        "sourceUrl": "",
        "skipDuplicates": True
    }
    
    # Make the API request
    url = f"{DELIB_API_BASE_URL}/projects/{project_id}/comments"
    try:
        response = requests.post(url, headers=DELIB_HEADERS, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error adding comment to Delib API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise

def get_stance_analysis_report(project_id: str, question_id: str) -> str:
    """
    Get the stance analysis report for a specific question.
    
    Args:
        project_id: The ID of the project
        question_id: The ID of the question
        
    Returns:
        The stance analysis report as a string
    """
    url = f"{DELIB_API_BASE_URL}/projects/{project_id}/questions/{question_id}/stance-analysis"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error getting stance analysis report: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise

def get_project_analysis_report(project_id: str) -> Dict:
    """
    Get the overall project analysis report.
    
    Args:
        project_id: The ID of the project
        
    Returns:
        The project analysis report
    """
    url = f"{DELIB_API_BASE_URL}/projects/{project_id}/analysis"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting project analysis report: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise

def generate_reply_with_stance_analysis(user_text: str, stance_report: str, conversation_history: List[Dict] = None) -> str:
    """
    Generate a reply based on the stance analysis report.
    
    Args:
        user_text: The text of the tweet to respond to
        stance_report: The stance analysis report (as a string)
        conversation_history: List of previous tweets in the conversation
        
    Returns:
        Generated reply text
    """
    # Format conversation history into messages
    messages = []
    
    # Create a system prompt that includes the stance analysis report
    system_prompt = """
    You are an engaging Twitter bot that facilitates thoughtful discussions by introducing alternative viewpoints and asking questions.
    
    Your goal is to respond to the user's message by acknowledging their point, introducing specific alternative viewpoints from other users, and then posing thought-provoking questions that invite further discussion.
    Keep your responses concise (under 280 characters) and directly related to the user's comment.
    
    IMPORTANT: Do not use Markdown link syntax (e.g., [text](url)) in your responses. Use plain text URLs instead.
    
    Below is an analysis of different stances on the topic the user is discussing:
    
    """
    
    # Add the stance report information to the system prompt
    if stance_report:
        system_prompt += stance_report
    
    system_prompt += """
    
    Based on this analysis:
    1. Briefly acknowledge the specific point the user made
    2. Share a concrete alternative viewpoint from the stance report, using phrases like "Others have pointed out that..." or "Some users with different views argue that..."
    3. Follow up with a thought-provoking question about this alternative perspective, such as "What do you think about this perspective?" or "How would you respond to this argument?"
    4. Stay focused on the exact topic the user mentioned - do not introduce tangential points
    5. Keep your response under 280 characters
    """
    
    # Add system message with instructions and stance report
    messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # Add conversation history if available
    if conversation_history:
        for tweet in conversation_history:
            messages.append({
                "role": "user" if tweet.get("username") != TARGET_USERNAME else "assistant",
                "content": tweet.get("text", "")
            })
    
    # Add the current user message
    messages.append({
        "role": "user",
        "content": user_text
    })
    
    print(f"Sending request to OpenRouter API with stance analysis context")
    
    # Call OpenRouter API
    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages
    )
    
    # Extract the generated reply
    reply = completion.choices[0].message.content
    
    # Convert any question:// URLs to full analytics URLs
    reply = convert_question_urls(reply)
    
    print(f"Generated reply with stance analysis: {reply}")
    return reply

def generate_reply_with_project_report(user_text: str, project_report: Dict, conversation_history: List[Dict] = None) -> str:
    """
    Generate a reply based on the overall project report.
    
    Args:
        user_text: The text of the tweet to respond to
        project_report: The project analysis report
        conversation_history: List of previous tweets in the conversation
        
    Returns:
        Generated reply text
    """
    # Format conversation history into messages
    messages = []
    
    # Create a system prompt that includes the project report
    system_prompt = """
    You are an engaging Twitter bot that facilitates thoughtful discussions by introducing alternative viewpoints and asking questions.
    
    Your goal is to respond to the user's specific message by acknowledging their point, sharing specific perspectives from other users, and then posing thought-provoking questions that invite further discussion.
    Keep your responses concise (under 280 characters) and highly relevant to what they actually said.
    
    IMPORTANT: Do not use Markdown link syntax (e.g., [text](url)) in your responses. Use plain text URLs instead.
    
    Below is an overview of the current discussion topics and perspectives:
    
    """
    
    # Add the project report information to the system prompt
    if project_report:
        system_prompt += json.dumps(project_report, ensure_ascii=False, indent=2)
    
    system_prompt += """
    
    Based on this overview:
    1. Briefly acknowledge the specific point or question in the user's message
    2. Share a concrete example of an alternative perspective from the project report, using phrases like "Several users have argued that..." or "One perspective from the discussion is that..."
    3. Follow up with a thought-provoking question about this perspective, such as "What's your take on this view?" or "How would you respond to this argument?"
    4. Try to stay focused on the topic the user brought up - do not introduce unrelated topics
    5. Keep your response under 280 characters
    """
    
    # Add system message with instructions and project report
    messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # Add conversation history if available
    if conversation_history:
        for tweet in conversation_history:
            messages.append({
                "role": "user" if tweet.get("username") != TARGET_USERNAME else "assistant",
                "content": tweet.get("text", "")
            })
    
    # Add the current user message
    messages.append({
        "role": "user",
        "content": user_text
    })
    
    print(f"Sending request to OpenRouter API with project report context")
    
    # Call OpenRouter API
    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages
    )
    
    # Extract the generated reply
    reply = completion.choices[0].message.content
    
    # Convert any question:// URLs to full analytics URLs
    reply = convert_question_urls(reply)
    
    print(f"Generated reply with project report: {reply}")
    return reply

def generate_continuation_message(conversation_history: List[Dict]) -> str:
    """
    Generate a message suggesting to continue the discussion at a URL,
    tailored to the specific conversation context.
    
    Args:
        conversation_history: List of previous tweets in the conversation
                             Each tweet is a dict with 'username' and 'text' keys
    
    Returns:
        Generated message text
    """
    # Create messages for the LLM
    messages = [
        {
            "role": "system",
            "content": f"""
            You are a helpful Twitter bot. The conversation has become quite long with {len(conversation_history)} messages.
            
            Generate a short, friendly message (under 280 characters) suggesting to continue the discussion at a URL.
            The message should be relevant to the specific topics and tone of the conversation.
            
            IMPORTANT: Do not use Markdown link syntax (e.g., [text](url)) in your responses. Use plain text URLs instead.
            
            Use phrases like "Let's continue this discussion about [TOPIC] at [URL]"
            or "This conversation about [TOPIC] is getting interesting! Let's move to [URL] to discuss further."
            
            Replace [TOPIC] with the main topic of the conversation, and [URL] with https://idobata.io/
            """
        }
    ]
    
    # Add conversation history if available
    if conversation_history:
        for tweet in conversation_history:
            messages.append({
                "role": "user" if tweet.get("username") != TARGET_USERNAME else "assistant",
                "content": tweet.get("text", "")
            })
    
    # Add the final user message asking for a continuation suggestion
    messages.append({
        "role": "user",
        "content": "Based on our conversation, suggest continuing this discussion at https://idobata.io/"
    })
    
    print(f"Generating continuation message based on conversation with {len(conversation_history)} messages")
    
    # Call OpenRouter API
    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages
    )
    
    # Extract the generated message
    message = completion.choices[0].message.content
    
    # Convert any question:// URLs to full analytics URLs
    message = convert_question_urls(message)
    
    print(f"Generated continuation message: {message}")
    return message

def generate_reply(user_text: str, conversation_history: List[Dict] = None, project_id: str = None) -> Optional[str]:
    """
    Generate a reply to a tweet using the Delib API and OpenRouter.
    
    Args:
        user_text: The text of the tweet to respond to
        conversation_history: List of previous tweets in the conversation
                             Each tweet is a dict with 'username' and 'text' keys
        project_id: The ID of the project in the Delib API
    
    Returns:
        Generated reply text or None if there was an error
    """
    # Print detailed information about input parameters
    print(f"=== GENERATE REPLY STARTED ===")
    print(f"User text: {user_text}")
    print(f"Project ID: {project_id}")
    if conversation_history:
        print(f"Conversation history: {len(conversation_history)} messages")
        for i, msg in enumerate(conversation_history):
            print(f"  Message {i+1}: {msg.get('username', 'Unknown')}: {msg.get('text', '')}")
    else:
        print("No conversation history provided")
    
    # Check if conversation history has 10 or more messages
    if conversation_history and len(conversation_history) >= 5:
        print(f"Conversation has {len(conversation_history)} messages, suggesting to continue at URL")
        return generate_continuation_message(conversation_history)
    
    if not project_id:
        print("Project ID is required")
        return None
    
    try:
        # Step 1: Add the comment to the Delib API
        print(f"\n=== STEP 1: Adding comment to Delib API ===")
        print(f"Project ID: {project_id}")
        print(f"User text: {user_text}")
        comment_response = add_comment_to_delib(project_id, user_text, conversation_history)

        print(f"Comment response:")
        print(json.dumps(comment_response, indent=2))
        
        # Check if we got any comments with stances back
        comments = comment_response.get("comments", [])
        print(f"\n=== STEP 2: Processing comments ===")
        print(f"Number of comments received: {len(comments)}")
        
        if not comments:
            print("No comments returned from Delib API, proceeding to use project report")
            # Continue to Case 2 instead of returning None
        
        # Print comment details
        for i, comment in enumerate(comments):
            comment_id = comment.get("id", "Unknown")
            content = comment.get("content", "")
            print(f"Comment {i+1} (ID: {comment_id}):")
            print(f"  Content: {content[:100]}..." if len(content) > 100 else f"  Content: {content}")
            
            # Print stance information
            stances = comment.get("stances", [])
            print(f"  Number of stances: {len(stances)}")
            print(stances)
            for j, stance in enumerate(stances):
                print(f"    Stance {j+1}:")
                print(f"      Question ID: {stance.get('questionId', 'Unknown')}")
                print(f"      Stance: {stance.get('stanceId', 'Unknown')}")
                print(f"      Confidence: {stance.get('confidence', 'Unknown')}")
        
        # Check if any comment has stances
        has_stances = False
        question_id = None
        
        for comment in comments:
            stances = comment.get("stances", [])
            # Filter out stances with stanceId "neutral"
            valid_stances = [s for s in stances if s.get("stanceId") != "neutral"]
            if valid_stances:
                has_stances = True
                # Get the first question ID with a valid stance
                question_id = valid_stances[0].get("questionId")
                break
        
        print(f"\n=== STEP 3: Determining reply strategy ===")
        print(f"Has stances: {has_stances}")
        print(f"Question ID: {question_id if question_id else 'None'}")
        
        # Case 1: If the comment matches a stance on a question
        if has_stances and question_id:
            print(f"\n=== STEP 4A: Using stance analysis ===")
            print(f"Comment matched stance on question {question_id}")
            
            # Get the stance analysis report
            print(f"Fetching stance analysis report for question {question_id}")
            stance_report = get_stance_analysis_report(project_id, question_id)
            
            # Print stance report summary
            print(f"Stance report received as string:")
            print(f"  Length: {len(stance_report)} characters")
            # Print first 100 characters as a preview
            preview = stance_report[:100] + "..." if len(stance_report) > 100 else stance_report
            print(f"  Preview: {preview}")
            
            # Generate reply using the stance analysis report
            print(f"\n=== STEP 5A: Generating reply with stance analysis ===")
            return generate_reply_with_stance_analysis(user_text, stance_report, conversation_history)
        
        # Case 2: If no comments were returned or no stance is matched
        else:
            print(f"\n=== STEP 4B: Using project report ===")
            if not comments:
                print(f"No comments returned from Delib API, using project report")
            else:
                print(f"Comments returned but did not match any stance, using project report")
            
            # Get the overall project report
            print(f"Fetching project analysis report")
            project_report = get_project_analysis_report(project_id)
            
            # Print project report summary
            print(f"Project report received:")
            questions = project_report.get('questions', [])
            print(f"  Number of questions in report: {len(questions)}")
            for i, question in enumerate(questions[:3]):  # Print first 3 questions
                print(f"    Question {i+1}: {question.get('text', 'Unknown')}")
                print(f"      Number of stances: {len(question.get('stances', []))}")
            
            # Generate reply using the project report
            print(f"\n=== STEP 5B: Generating reply with project report ===")
            return generate_reply_with_project_report(user_text, project_report, conversation_history)
            
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Error generating reply: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None
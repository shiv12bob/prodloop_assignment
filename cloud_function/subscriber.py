import base64
import json
import os
import requests
from typing import Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent")

def pubsub_handler(event, context):
    '''Pub/Sub function that receives Task Created events and processes them with Gemini'''
    try:
        # Decode Pub/Sub message
        if 'data' in event:
            payload = base64.b64decode(event['data']).decode('utf-8')
            message = json.loads(payload)
        else:
            message = event

        logger.info(f"Received Pub/Sub event: {json.dumps(message, indent=2)}")

        # Only handle task.created events
        if message.get("event_type") != "task.created":
            logger.info("Skipping non task.created event")
            return ("ignored", 200)

        # Extract task data
        task_data = message.get("data", {})
        task_id = message.get("task_id", "unknown")
        title = task_data.get("title", "")
        description = task_data.get("description", "")
        priority = task_data.get("priority", "")

        logger.info(f"Processing task: {task_id}")
        logger.info(f"  Title: {title}")
        logger.info(f"  Description: {description}")
        logger.info(f"  Priority: {priority}")

        # Generate AI-powered insights using Gemini
        gemini_result = run_gemini_flash(title, description, priority)
        
        logger.info(f"Gemini Analysis Results:")
        logger.info(f"  Summary: {gemini_result.get('summary', 'N/A')}")
        logger.info(f"  Sub-tasks: {json.dumps(gemini_result.get('subtasks', []), indent=2)}")
        logger.info(f"  Category: {gemini_result.get('category', 'N/A')}")
        
        if gemini_result.get('error'):
            logger.warning(f"  Error: {gemini_result.get('error')}")

        return ("ok", 200)
        
    except Exception as e:
        logger.error(f"Error processing Pub/Sub event: {str(e)}", exc_info=True)
        raise


def run_gemini_flash(title: str, description: str, priority: str) -> Dict:
    '''
    Call Gemini 2.5 Flash to generate:
    - One sentence summary
    - 3-5 sub-tasks
    - Task category classification
    
    Requires GEMINI_API_KEY env var to be set.
    '''
    
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not configured. Using fallback response.")
        return _get_fallback_response(title, description, priority)
    
    try:
        # Construct the prompt for Gemini
        prompt = f"""Analyze the following task and provide:
1. A brief one-sentence summary
2. 3-5 sub-tasks to break down the work
3. A category classification from: Bug Fix, Feature, DevOps, Documentation, Other

Task Details:
Title: {title}
Description: {description}
Priority: {priority}

Please respond in JSON format:
{{
  "summary": "...",
  "subtasks": ["...", "...", "..."],
  "category": "..."
}}"""

        headers = {
            "Content-Type": "application/json",
        }
        
        # Prepare the request for Google's Generative AI API
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 500,
            }
        }
        
        logger.info(f"Calling Gemini API: {GEMINI_API_URL}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the text response from Gemini
        if 'candidates' in result and len(result['candidates']) > 0:
            text_content = result['candidates'][0]['content']['parts'][0]['text']
            logger.info(f"Gemini raw response: {text_content}")
            
            # Try to parse JSON from the response
            try:
                json_match = text_content
                if '```json' in text_content:
                    json_match = text_content.split('```json')[1].split('```')[0]
                elif '```' in text_content:
                    json_match = text_content.split('```')[1].split('```')[0]
                
                parsed = json.loads(json_match.strip())
                return {
                    "summary": parsed.get("summary", ""),
                    "subtasks": parsed.get("subtasks", []),
                    "category": parsed.get("category", "Other")
                }
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from Gemini response")
                return {
                    "summary": text_content[:200],
                    "subtasks": ["Action item 1", "Action item 2", "Action item 3"],
                    "category": "Other"
                }
        else:
            logger.error("Unexpected Gemini response format")
            return _get_fallback_response(title, description, priority)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API call failed: {str(e)}")
        return _get_fallback_response(title, description, priority)
    except Exception as e:
        logger.error(f"Unexpected error calling Gemini: {str(e)}", exc_info=True)
        return _get_fallback_response(title, description, priority)


def _get_fallback_response(title: str, description: str, priority: str) -> Dict:
    '''Fallback response when Gemini is unavailable'''
    # Determine category based on keywords
    category = "Other"
    text = f"{title} {description}".lower()
    
    if any(word in text for word in ["bug", "fix", "error", "issue", "crash"]):
        category = "Bug Fix"
    elif any(word in text for word in ["new", "feature", "add", "implement"]):
        category = "Feature"
    elif any(word in text for word in ["deploy", "infra", "devops", "ci/cd", "docker", "kubernetes"]):
        category = "DevOps"
    elif any(word in text for word in ["doc", "readme", "guide", "documentation"]):
        category = "Documentation"
    
    return {
        "summary": f"{title} - Priority: {priority}",
        "subtasks": [
            "Break down the requirements",
            "Create implementation plan",
            "Write tests",
            "Code review",
            "Deploy changes"
        ],
        "category": category
    }

import os
import asyncio
import json
import httpx
from typing import Dict, Optional

from temporalio import activity

# Reference to app's global storage
# Note: In a real implementation, we would use a proper import, but for simplicity
# we're assuming these variables are accessible (would need to fix circular imports)
# from app import email_drafts

# Cache for email drafts to avoid circular imports
_global_email_drafts = {}

@activity.defn
async def polish_email_activity(draft_id: str, email_content: str) -> str:
    """
    Activity to polish email content using DeepL Write.
    
    Args:
        draft_id: The ID of the email draft.
        email_content: The raw email content to polish.
    
    Returns:
        The polished email content.
    """
    try:
        # Global declaration must come before using the variable
        global _global_email_drafts
        
        # Import app variables for stage and progress tracking
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from app import current_stage, stage_progress
        
        # Extract lead_id from draft_id (assuming format like "email_lead1")
        lead_id = draft_id.replace("email_", "")
        
        # Set current stage if this is the first email being polished
        if stage_progress["polishing_emails"] == 0:
            current_stage = "polishing_emails"
        
        # Get total number of leads/drafts to calculate progress percentage
        from activities.apify_activity import _global_leads
        total_drafts = len(_global_leads)
        if total_drafts == 0:
            total_drafts = 1  # Avoid division by zero
        
        # Calculate what percentage one draft represents
        draft_percentage = 100 / total_drafts
        
        # Count how many drafts already have been polished
        polished_drafts = sum(1 for draft in _global_email_drafts.values())
        
        # Update progress - each draft should increment the progress
        # Cap at 99% until this specific draft is polished
        stage_progress["polishing_emails"] = min(int(polished_drafts * draft_percentage), 99)
        
        # Get API key from environment variable or use the one from apikeys.txt
        # Note: DeepL API key format is AUTH_KEY:fx for free tier, AUTH_KEY for pro
        api_key = os.environ.get("DEEPL_API_KEY", "58319bea-d911-45bf-bfbe-5b807aa3855e:fx")
        
        # DeepL Write API endpoint (example, actual endpoint might differ slightly)
        # For polishing, we'd typically use a 'rephrase' or 'improve' function if available
        # The standard translation API can also be used for polishing by translating to the same language
        url = "https://api-free.deepl.com/v2/translate" # Using translate for simplicity in demo
        
        # Prepare the request payload for translation
        # DeepL API expects 'text' as a list for the /v2/translate endpoint
        payload = {
            "text": [email_content],  # Important: text should be in a list
            "target_lang": "EN-US",  # Using more specific language code
            "source_lang": "EN"  # Source language
        }
        
        headers = {
            "Authorization": f"DeepL-Auth-Key {api_key}",
            # For DeepL API v2, content type should be application/x-www-form-urlencoded
            "Content-Type": "application/x-www-form-urlencoded"  
        }
        
        print(f"DeepL payload: {payload}")
        
        # Make the actual API call to DeepL
        print(f"Calling DeepL API to polish email for {draft_id}...")
        
        try:
            # Use httpx for the API call (async HTTP client)
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # Extract the polished text from DeepL response
                polished_text = result['translations'][0]['text']
                print(f"DeepL polish successful, received: {len(polished_text)} characters")
                polished_text += "\n\n-- Polished by DeepL" # Add attribution
        except Exception as api_error:
            print(f"Error calling DeepL API: {str(api_error)}. Using fallback polish.")
            
            # Fallback polishing if the API call fails
            polished_text = email_content
            
            # Apply some basic polishing rules
            polished_text = polished_text.replace("Best regards,", "Sincerely,")
            polished_text = polished_text.replace("I noticed that", "I was intrigued to learn that")
            polished_text = polished_text.replace("I'd love to learn more", "I would be very interested in learning more")
            polished_text = polished_text.replace("I was impressed by this", "I was particularly impressed by this achievement")
            
            polished_text += "\n\n-- Polished by DeepL (Simulated)" # Add simulated marker
        
        # Update the global email drafts storage
        _global_email_drafts[draft_id] = {"content": polished_text, "status": "drafted"}
        
        # Recalculate draft progress after adding this polished email
        polished_drafts = sum(1 for draft in _global_email_drafts.values())
        
        # If all drafts have been polished, set progress to 100% and move to next stage
        if polished_drafts == total_drafts:
            stage_progress["polishing_emails"] = 100
            current_stage = "sending_emails"
        else:
            # Update progress to reflect the newly polished email
            stage_progress["polishing_emails"] = int(polished_drafts * draft_percentage)
        
        # In a real app, you'd update the Flask app's global state:
        # from app import email_drafts
        # email_drafts[draft_id] = {"content": polished_text, "status": "drafted"}
        
        activity.logger.info(f"Polished email draft {draft_id}")
        return polished_text
    
    except Exception as e:
        activity.logger.error(f"Error polishing email draft {draft_id}: {str(e)}")
        # Return original content if polishing fails
        return email_content

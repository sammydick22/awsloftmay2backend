import os
import asyncio
import json
import httpx
from typing import Dict, Optional

from temporalio import activity

# Reference to app's global storage
# Note: In a real implementation, we would use a proper import, but for simplicity
# we're assuming these variables are accessible (would need to fix circular imports)
# from app import email_drafts, leads, workflow_status

# Cache for email drafts and leads to avoid circular imports
from activities.apify_activity import _global_leads
from activities.deepl_activity import _global_email_drafts

@activity.defn
async def send_email_activity(lead_id: str, recipient_email: str, email_content: str) -> Dict:
    """
    Activity to simulate sending an email using Arcade.dev tool-calling.
    
    Args:
        lead_id: The ID of the lead associated with the email.
        recipient_email: The email address of the recipient.
        email_content: The content of the email to send.
    
    Returns:
        A dictionary indicating the status of the send operation.
    """
    try:
        # Global declarations must come before using the variables
        global _global_email_drafts, _global_leads
        
        # Import app variables for stage and progress tracking
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from app import current_stage, stage_progress, workflow_status
        
        # Set current stage if this is the first email being sent
        if stage_progress["sending_emails"] == 0:
            current_stage = "sending_emails"
        
        # Get total number of leads to calculate progress percentage
        total_leads = len(_global_leads)
        if total_leads == 0:
            total_leads = 1  # Avoid division by zero
        
        # Calculate what percentage one lead represents
        lead_percentage = 100 / total_leads
        
        # Count how many emails already have been sent
        sent_emails = sum(1 for lead in _global_leads.values() if lead.get("status") == "sent")
        
        # Update progress - each email sent should increment the progress
        # Cap at 99% until this specific email is sent
        stage_progress["sending_emails"] = min(int(sent_emails * lead_percentage), 99)
        
        # Get API key from environment variable or use the one from apikeys.txt
        api_key = os.environ.get("ARCADE_API_KEY", "arc_o1R1yGvUypGZr8mjfFwpWng8GqtVzNc2DPe3AYQ2mgtsLs0PXzjv")
        
        # Arcade.dev Tool Calling API endpoint (example)
        url = "https://api.arcade.dev/v1/tool_calls" # Example endpoint
        
        # Prepare the payload for the "Send Email" tool
        # Assuming a tool named "Google.SendEmail" or similar is configured in Arcade
        payload = {
            "tool_name": "Google.SendEmail", # Example tool name
            "parameters": {
                "to": recipient_email,
                "subject": email_content.splitlines()[0].replace("Subject: ", ""), # Extract subject from content
                "body": email_content,
                # Add other parameters as required by the tool (e.g., from, cc, bcc)
            }
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Simulate API call for the hackathon demo
        # In real implementation, this would be:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(url, json=payload, headers=headers)
        #     response.raise_for_status()
        #     result = response.json()
        #     send_status = result.get("status", "unknown") # Assuming Arcade returns a status

        # Simulate API delay
        await asyncio.sleep(1.5)
        
        # Simulate successful send for the demo
        send_status = "sent"
        
        # Update the global email drafts storage with the final status
        draft_id = f"email_{lead_id}"
        if draft_id in _global_email_drafts:
            _global_email_drafts[draft_id]["status"] = send_status
        
        # Also update the lead's status directly for easier frontend access
        if lead_id in _global_leads:
             _global_leads[lead_id]["status"] = send_status
             _global_leads[lead_id]["email_content"] = email_content # Add email content to lead for /state endpoint
        
        # Recalculate progress after sending this email
        sent_emails = sum(1 for lead in _global_leads.values() if lead.get("status") == "sent")
        
        # If all emails have been sent, set progress to 100% and mark workflow as completed
        if sent_emails == total_leads:
            stage_progress["sending_emails"] = 100
            current_stage = "completed"
            workflow_status = "completed"
        else:
            # Update progress to reflect the newly sent email
            stage_progress["sending_emails"] = int(sent_emails * lead_percentage)
        
        # In a real app without circular imports, you'd do:
        # from app import email_drafts, leads, current_stage, stage_progress, workflow_status
        # draft_id = f"email_{lead_id}"
        # if draft_id in email_drafts:
        #     email_drafts[draft_id]["status"] = send_status
        # if lead_id in leads:
        #     leads[lead_id]["status"] = send_status
        #     leads[lead_id]["email_content"] = email_content
        
        activity.logger.info(f"Simulated sending email for lead {lead_id} to {recipient_email}. Status: {send_status}")
        return {"status": send_status}
    
    except Exception as e:
        activity.logger.error(f"Error simulating sending email for lead {lead_id}: {str(e)}")
        send_status = "failed"
        
        # Update the global email drafts storage with the failed status
        draft_id = f"email_{lead_id}"
        if draft_id in _global_email_drafts:
            _global_email_drafts[draft_id]["status"] = send_status
            
        # Also update the lead's status directly
        if lead_id in _global_leads:
             _global_leads[lead_id]["status"] = send_status
             _global_leads[lead_id]["email_content"] = email_content # Still add content even if failed
             
        return {"status": send_status, "error": str(e)}

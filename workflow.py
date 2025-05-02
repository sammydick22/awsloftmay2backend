import asyncio
from datetime import timedelta
from typing import Dict, List

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

# Note: Activities are imported directly in the execution context,
# not at the module level to avoid circular imports

# We don't import app globals directly here to avoid circular imports
# Activities will update the global variables themselves


@workflow.defn
class OutboundProspectingWorkflow:
    """Workflow for outbound sales prospecting."""

    @workflow.run
    async def run(self) -> Dict:
        """Execute the outbound prospecting workflow."""
        # Import activities here to avoid circular imports
        from activities.apify_activity import fetch_leads_activity
        from activities.perplexity_activity import generate_insight_activity
        from activities.deepl_activity import polish_email_activity
        from activities.arcade_activity import send_email_activity
        
        try:
            # Step 1: Fetch leads from Apify
            fetched_leads = await workflow.execute_activity(
                fetch_leads_activity,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    non_retryable_error_types=["ValidationError"],
                ),
            )
            
            # Process leads in parallel for faster completion
            insight_tasks = []
            
            # Step 2: Generate insights for each lead with Perplexity Sonar
            for lead_id, lead in fetched_leads.items():
                insight_task = workflow.execute_activity(
                    generate_insight_activity,
                    lead_id,
                    lead["name"],
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
                insight_tasks.append(insight_task)
            
            # Wait for all insight tasks to complete
            await asyncio.gather(*insight_tasks)
            
            # Now process email composition, polishing, and sending sequentially for each lead
            for lead_id, lead in fetched_leads.items():
                # Step 3: Compose email draft (done directly here since it's simple string manipulation)
                email_template = f"""Subject: Quick question about {lead['name']}

Hi {lead['name']},

I noticed that {lead.get('insight', 'your company is doing some innovative work')}. I was impressed by this and it inspired me to reach out.
At [Your Company], we specialize in solutions that could help your team streamline operations and boost productivity.

I'd love to learn more about your current challenges and see if there might be a fit. Would you be open to a brief conversation next week?

Best regards,
[Your Name]
[Your Company]
                """
                
                # Store the draft
                draft_id = f"email_{lead_id}"
                # This would normally update the global email_drafts dictionary
                
                # Step 4: Polish the email with DeepL
                polished_email = await workflow.execute_activity(
                    polish_email_activity,
                    draft_id,
                    email_template,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
                
                # Step 5: Send the email via Arcade.dev
                send_result = await workflow.execute_activity(
                    send_email_activity,
                    lead_id,
                    lead.get('email', f"{lead['name'].lower().replace(' ', '.')}@example.com"),  # Fallback mock email
                    polished_email,
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )
            
            # Mark workflow as completed
            # This would be done externally when processing completes
            return {"status": "completed", "message": "All leads processed successfully"}
        
        except Exception as e:
            # Log error and return failure
            error_msg = f"Workflow failed: {str(e)}"
            return {"status": "failed", "message": error_msg}

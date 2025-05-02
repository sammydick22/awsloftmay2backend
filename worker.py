import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from workflow import OutboundProspectingWorkflow
from activities.apify_activity import fetch_leads_activity
from activities.perplexity_activity import generate_insight_activity
from activities.deepl_activity import polish_email_activity
from activities.arcade_activity import send_email_activity

# Global variable to store the reference to the running worker
WORKER = None

async def run_worker():
    """Run the Temporal worker to execute activities."""
    global WORKER
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Connect to the Temporal server
    client = await Client.connect("localhost:7233")
    
    # Create a worker on the "prospect_queue" task queue
    worker = Worker(
        client,
        task_queue="prospect_queue",
        workflows=[OutboundProspectingWorkflow],
        activities=[
            fetch_leads_activity,
            generate_insight_activity,
            polish_email_activity,
            send_email_activity,
        ],
    )
    
    # Start the worker (runs until cancelled)
    WORKER = worker
    await worker.run()

if __name__ == "__main__":
    # Run the worker
    asyncio.run(run_worker())

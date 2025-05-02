import json
import unittest
import asyncio
import sys
import os
import time
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from worker import run_worker


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete backend system."""

    def setUp(self):
        """Set up test environment."""
        # Create a Flask test client
        self.app = app.test_client()
        self.app.testing = True
        
        # Set up an event loop for async operations
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Reset the application state
        from app import leads, email_drafts, workflow_status, current_stage, stage_progress
        from activities.apify_activity import _global_leads
        from activities.deepl_activity import _global_email_drafts
        
        # Clear both app-level and module-level variables
        leads.clear()
        email_drafts.clear()
        _global_leads.clear()
        _global_email_drafts.clear()
        
        # Reset status variables
        workflow_status = "idle"
        current_stage = "idle"
        
        # Reset progress for all stages
        for stage in stage_progress:
            stage_progress[stage] = 0

    def tearDown(self):
        """Clean up after tests."""
        self.loop.close()

    @patch('worker.Client.connect')
    @patch('app.connect_temporal')
    @patch('worker.Worker')
    def test_full_workflow(self, mock_worker, mock_connect_temporal, mock_worker_client_connect):
        """Test the entire workflow from start to finish."""
        # Mock the temporal client and worker to avoid actually starting Temporal
        mock_client = MagicMock()
        mock_worker_instance = MagicMock()
        mock_worker.return_value = mock_worker_instance
        
        # Mock the client.connect function to return our mock client
        connect_future = asyncio.Future()
        connect_future.set_result(mock_client)
        mock_connect_temporal.return_value = connect_future
        mock_worker_client_connect.return_value = connect_future
        
        # Mock the start_workflow method
        mock_client.start_workflow = MagicMock()
        start_workflow_future = asyncio.Future()
        start_workflow_future.set_result(None)
        mock_client.start_workflow.return_value = start_workflow_future
        
        # Setup mock activities to actually execute (simplified versions)
        async def mock_apify_activity():
            """Mock implementation of fetch_leads_activity."""
            from app import leads
            mock_leads = {
                "lead1": {
                    "id": "lead1",
                    "name": "Acme Corporation",
                    "website": "https://acme.example.com",
                    "industry": "Technology",
                    "location": "San Francisco, CA"
                }
            }
            # Update the global leads
            leads.update(mock_leads)
            from activities.apify_activity import _global_leads
            _global_leads.update(mock_leads)
            return mock_leads
        
        async def mock_perplexity_activity(lead_id, company_name):
            """Mock implementation of generate_insight_activity."""
            from app import leads
            insight = f"{company_name} has recently launched an innovative product."
            # Update the lead with the insight
            if lead_id in leads:
                leads[lead_id]["insight"] = insight
            from activities.apify_activity import _global_leads
            if lead_id in _global_leads:
                _global_leads[lead_id]["insight"] = insight
            return insight
        
        async def mock_deepl_activity(draft_id, email_content):
            """Mock implementation of polish_email_activity."""
            from app import email_drafts
            polished_email = f"Polished: {email_content}"
            # Store in the email drafts
            email_drafts[draft_id] = {"content": polished_email, "status": "drafted"}
            from activities.deepl_activity import _global_email_drafts
            _global_email_drafts[draft_id] = {"content": polished_email, "status": "drafted"}
            return polished_email
        
        async def mock_arcade_activity(lead_id, recipient_email, email_content):
            """Mock implementation of send_email_activity."""
            from app import leads, email_drafts
            # Mark the email as sent
            draft_id = f"email_{lead_id}"
            if draft_id in email_drafts:
                email_drafts[draft_id]["status"] = "sent"
            if lead_id in leads:
                leads[lead_id]["status"] = "sent"
                leads[lead_id]["email_content"] = email_content
            
            from activities.deepl_activity import _global_email_drafts
            from activities.apify_activity import _global_leads
            if draft_id in _global_email_drafts:
                _global_email_drafts[draft_id]["status"] = "sent"
            if lead_id in _global_leads:
                _global_leads[lead_id]["status"] = "sent"
                _global_leads[lead_id]["email_content"] = email_content
            
            return {"status": "sent"}
        
        # Patch the actual activities with our simplified mock implementations
        with patch('activities.apify_activity.fetch_leads_activity', side_effect=mock_apify_activity), \
             patch('activities.perplexity_activity.generate_insight_activity', side_effect=mock_perplexity_activity), \
             patch('activities.deepl_activity.polish_email_activity', side_effect=mock_deepl_activity), \
             patch('activities.arcade_activity.send_email_activity', side_effect=mock_arcade_activity):
            
            # Start the workflow via the REST API
            response = self.app.post('/start')
            self.assertEqual(response.status_code, 200)
            
            # Parse the response
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'started')
            
            # Manually trigger the workflow steps to simulate what would happen
            # in a real environment when Temporal executes the activities
            from app import workflow_status
            workflow_status = "in_progress"  # Simulate state transition
            
            # Simulate Temporal executing the fetch_leads_activity
            self.loop.run_until_complete(mock_apify_activity())
            
            # Check state to confirm leads are there
            response = self.app.get('/state')
            data = json.loads(response.data)
            self.assertEqual(len(data['leads']), 1)
            self.assertEqual(data['leads'][0]['name'], 'Acme Corporation')
            
            # Simulate Temporal executing the generate_insight_activity
            self.loop.run_until_complete(mock_perplexity_activity("lead1", "Acme Corporation"))
            
            # Check state to confirm insight is added
            response = self.app.get('/state')
            data = json.loads(response.data)
            self.assertIn('insight', data['leads'][0])
            
            # Simulate composing and polishing an email
            draft_id = "email_lead1"
            email_content = "Test email content"
            self.loop.run_until_complete(mock_deepl_activity(draft_id, email_content))
            
            # Simulate sending the email
            self.loop.run_until_complete(mock_arcade_activity("lead1", "acme@example.com", "Polished: Test email content"))
            
            # Set workflow status to completed
            workflow_status = "completed"
            
            # Check final state to confirm email was sent
            response = self.app.get('/state')
            data = json.loads(response.data)
            self.assertEqual(data['workflowStatus'], 'completed')
            self.assertEqual(data['leads'][0]['status'], 'sent')
            
            # Test reset functionality
            response = self.app.post('/reset')
            self.assertEqual(response.status_code, 200)
            
            # Verify state was reset
            response = self.app.get('/state')
            data = json.loads(response.data)
            self.assertEqual(len(data['leads']), 0)
            self.assertEqual(data['workflowStatus'], 'idle')


if __name__ == '__main__':
    unittest.main()

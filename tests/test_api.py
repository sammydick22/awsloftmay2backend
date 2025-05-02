import json
import unittest
from unittest.mock import patch, MagicMock
import asyncio
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


class TestFlaskAPI(unittest.TestCase):
    """Test cases for the Flask API endpoints."""

    def setUp(self):
        """Set up test client and other test variables."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Reset the global variables before each test
        from app import leads, email_drafts, workflow_status, current_stage, stage_progress
        leads.clear()
        email_drafts.clear()
        
        # Reset global variables in app module
        workflow_status = "idle"
        current_stage = "idle"
        
        # Reset progress for all stages
        for stage in stage_progress:
            stage_progress[stage] = 0

    def test_state_endpoint_no_leads(self):
        """Test the /state endpoint when no leads exist."""
        response = self.app.get('/state')
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Verify the structure and content
        self.assertIn('leads', data)
        self.assertIn('workflowStatus', data)
        self.assertEqual(data['workflowStatus'], 'idle')
        self.assertEqual(len(data['leads']), 0)

    def test_state_endpoint_with_leads(self):
        """Test the /state endpoint when leads exist."""
        # Add some test leads to the global variable
        from app import leads, email_drafts, _global_leads, _global_email_drafts
        
        test_lead = {
            "id": "test_lead",
            "name": "Test Company",
            "website": "https://test.example.com",
            "industry": "Technology",
            "location": "Test Location",
            "insight": "Test insight about the company."
        }
        
        # Update both global and module-level variables
        leads["test_lead"] = test_lead
        _global_leads["test_lead"] = test_lead
        
        # Create email draft
        email_draft = {
            "content": "Test email content",
            "status": "pending"
        }
        
        # Update both variables
        email_drafts["email_test_lead"] = email_draft 
        _global_email_drafts["email_test_lead"] = email_draft
        
        response = self.app.get('/state')
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Verify the structure and content
        self.assertIn('leads', data)
        self.assertEqual(len(data['leads']), 1)
        self.assertEqual(data['leads'][0]['name'], 'Test Company')
        self.assertEqual(data['leads'][0]['email_content'], 'Test email content')
        self.assertEqual(data['leads'][0]['status'], 'pending')

    def test_reset_endpoint(self):
        """Test the /reset endpoint."""
        # Add some test data to be reset
        from app import leads, email_drafts, workflow_status
        leads["test_lead"] = {"id": "test_lead", "name": "Test Company"}
        email_drafts["email_test_lead"] = {"content": "Test email", "status": "sent"}
        
        # Set workflow status to completed using the variable from app module
        workflow_status = "completed"
        
        response = self.app.post('/reset')
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'reset')
        
        # Verify that the global variables were reset
        from app import leads, email_drafts, workflow_status
        self.assertEqual(len(leads), 0)
        self.assertEqual(len(email_drafts), 0)
        self.assertEqual(workflow_status, 'idle')

    @patch('app.connect_temporal')
    @patch('workflow.OutboundProspectingWorkflow')
    def test_start_endpoint(self, mock_workflow, mock_connect_temporal):
        """Test the /start endpoint."""
        # Mock the asynchronous functions and client
        mock_client = MagicMock()
        future = asyncio.Future()
        future.set_result(mock_client)
        mock_connect_temporal.return_value = future
        
        # Mock the start_workflow method
        mock_client.start_workflow = MagicMock()
        start_workflow_future = asyncio.Future()
        start_workflow_future.set_result(None)
        mock_client.start_workflow.return_value = start_workflow_future
        
        # Flask test client doesn't support async requests directly,
        # so we need to patch the actual function that handles the endpoint
        with patch('app.start_workflow', side_effect=lambda: {"status": "started", "workflow_id": "test-workflow-id"}):
            response = self.app.post('/start')
            
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'started')
        self.assertIn('workflow_id', data)


if __name__ == '__main__':
    unittest.main()

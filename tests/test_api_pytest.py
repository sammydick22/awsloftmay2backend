"""
Pytest-based tests for the Flask API endpoints.
These tests use the pytest fixtures defined in conftest.py.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import asyncio


@pytest.mark.usefixtures("reset_app_state")
class TestAPIEndpoints:
    """Tests for the Flask API endpoints using pytest."""
    
    def test_state_endpoint_no_leads(self, flask_app):
        """Test the /state endpoint when no leads exist."""
        response = flask_app.get('/state')
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Verify the structure and content
        assert 'leads' in data
        assert 'workflowStatus' in data
        assert data['workflowStatus'] == 'idle'
        assert len(data['leads']) == 0
    
    def test_state_endpoint_with_leads(self, flask_app):
        """Test the /state endpoint when leads exist."""
        # Add some test leads to the global variable
        from app import leads, email_drafts
        leads["test_lead"] = {
            "id": "test_lead",
            "name": "Test Company",
            "website": "https://test.example.com",
            "industry": "Technology",
            "location": "Test Location",
            "insight": "Test insight about the company."
        }
        
        email_drafts["email_test_lead"] = {
            "content": "Test email content",
            "status": "pending"
        }
        
        response = flask_app.get('/state')
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Verify the structure and content
        assert 'leads' in data
        assert len(data['leads']) == 1
        assert data['leads'][0]['name'] == 'Test Company'
        assert data['leads'][0]['email_content'] == 'Test email content'
        assert data['leads'][0]['status'] == 'pending'
    
    def test_reset_endpoint(self, flask_app):
        """Test the /reset endpoint."""
        # Add some test data to be reset
        from app import leads, email_drafts, workflow_status
        leads["test_lead"] = {"id": "test_lead", "name": "Test Company"}
        email_drafts["email_test_lead"] = {"content": "Test email", "status": "sent"}
        workflow_status = "completed"
        
        response = flask_app.post('/reset')
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        assert data['status'] == 'reset'
        
        # Verify that the global variables were reset
        from app import leads, email_drafts, workflow_status
        assert len(leads) == 0
        assert len(email_drafts) == 0
    
    @pytest.mark.asyncio
    async def test_start_endpoint(self, flask_app, monkeypatch):
        """Test the /start endpoint."""
        # Create a mock for the connect_temporal function
        mock_client = MagicMock()
        mock_future = asyncio.Future()
        mock_future.set_result(mock_client)
        
        # Create a mock for the start_workflow method
        workflow_future = asyncio.Future()
        workflow_future.set_result(None)
        mock_client.start_workflow = MagicMock(return_value=workflow_future)
        
        # Patch the connect_temporal function to return our mock client
        async def mock_connect():
            return mock_client
        
        monkeypatch.setattr('app.connect_temporal', mock_connect)
        
        # Patch the start_workflow function to avoid circular imports with OutboundProspectingWorkflow
        def mock_start_workflow():
            from app import workflow_status
            workflow_status = "in_progress"
            return {"status": "started", "workflow_id": "test-workflow-id"}
        
        monkeypatch.setattr('app.start_workflow', mock_start_workflow)
        
        # Make the request to start the workflow
        response = flask_app.post('/start')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'started'


@pytest.mark.usefixtures("reset_app_state")
class TestAPIErrorHandling:
    """Tests for API error handling."""
    
    @pytest.mark.asyncio
    async def test_start_endpoint_error(self, flask_app, monkeypatch):
        """Test error handling in the /start endpoint."""
        # Patch the connect_temporal function to raise an exception
        async def mock_connect_error():
            raise Exception("Temporal connection error")
        
        monkeypatch.setattr('app.connect_temporal', mock_connect_error)
        
        # Make the request to start the workflow
        response = flask_app.post('/start')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'message' in data

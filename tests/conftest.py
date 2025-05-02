"""
Pytest configuration file for the Outbound Sales Prospector backend tests.

This file contains fixtures and configuration that are shared across test files.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch
from temporalio.testing import WorkflowEnvironment
from temporalio.client import Client

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


@pytest.fixture
def flask_app():
    """Fixture for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def reset_app_state():
    """Fixture to reset application state between tests."""
    from app import leads, email_drafts, workflow_status
    
    # Save original state
    original_leads = leads.copy()
    original_email_drafts = email_drafts.copy()
    original_workflow_status = workflow_status
    
    # Clear state for test
    leads.clear()
    email_drafts.clear()
    app.workflow_status = "idle"
    
    yield
    
    # Restore original state after test
    leads.clear()
    leads.update(original_leads)
    email_drafts.clear()
    email_drafts.update(original_email_drafts)
    app.workflow_status = original_workflow_status


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def temporal_env():
    """Fixture for Temporal testing environment."""
    env = await WorkflowEnvironment.start_local()
    try:
        yield env
    finally:
        await env.shutdown()


@pytest.fixture
async def temporal_client(temporal_env):
    """Fixture for Temporal client."""
    yield temporal_env.client


@pytest.fixture
def mock_apify_client():
    """Fixture for mocked Apify client."""
    with patch('activities.apify_activity.ApifyClient') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_perplexity_api():
    """Fixture for mocked Perplexity API."""
    with patch('activities.perplexity_activity.httpx.AsyncClient.post') as mock:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test insight about the company."
                }
            }]
        }
        mock.return_value.__aenter__.return_value = mock_response
        yield mock


@pytest.fixture
def mock_deepl_api():
    """Fixture for mocked DeepL API."""
    with patch('activities.deepl_activity.httpx.AsyncClient.post') as mock:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "translations": [{
                "text": "Polished test email content."
            }]
        }
        mock.return_value.__aenter__.return_value = mock_response
        yield mock


@pytest.fixture
def mock_arcade_api():
    """Fixture for mocked Arcade API."""
    with patch('activities.arcade_activity.httpx.AsyncClient.post') as mock:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "status": "sent"
        }
        mock.return_value.__aenter__.return_value = mock_response
        yield mock

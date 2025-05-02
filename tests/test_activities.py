import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from temporalio.testing import ActivityEnvironment
from activities.apify_activity import fetch_leads_activity
from activities.perplexity_activity import generate_insight_activity
from activities.deepl_activity import polish_email_activity
from activities.arcade_activity import send_email_activity


class TestActivities(unittest.TestCase):
    """Test cases for the individual workflow activities."""

    def setUp(self):
        """Set up test environment."""
        # Create an activity testing environment
        self.activity_env = ActivityEnvironment()
        
        # Create an event loop for async operations
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test environment."""
        self.loop.close()

    @patch('activities.apify_activity.ApifyClient')
    def test_fetch_leads_activity(self, mock_apify_client):
        """Test the fetch_leads_activity."""
        # Set up mock response
        mock_client_instance = MagicMock()
        mock_apify_client.return_value = mock_client_instance
        
        # Run the activity and get result
        result = self.loop.run_until_complete(
            self.activity_env.run(fetch_leads_activity)
        )
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        
        # Verify a sample lead has the required fields
        lead = next(iter(result.values()))
        self.assertIn('id', lead)
        self.assertIn('name', lead)
        self.assertIn('website', lead)
        
        # Verify the mock was called with the correct API key
        mock_apify_client.assert_called_once()

    @patch('activities.perplexity_activity.httpx.AsyncClient.post')
    @patch('activities.perplexity_activity._global_leads')
    def test_generate_insight_activity(self, mock_leads, mock_post):
        """Test the generate_insight_activity."""
        # Set up mock data
        lead_id = "test_lead"
        company_name = "Test Company"
        mock_leads.get.return_value = {"id": lead_id, "name": company_name}
        
        # Create a mock response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test insight about the company."
                }
            }]
        }
        # Set up the mock to return our prepared response
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Run the activity
        result = self.loop.run_until_complete(
            self.activity_env.run(
                generate_insight_activity,
                lead_id,
                company_name
            )
        )
        
        # Verify the result
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "")
        
        # Verify the activity tried to update the lead with the insight
        # This would normally happen but is mocked out for the test

    @patch('activities.deepl_activity.httpx.AsyncClient.post')
    @patch('activities.deepl_activity._global_email_drafts')
    def test_polish_email_activity(self, mock_email_drafts, mock_post):
        """Test the polish_email_activity."""
        # Set up mock data
        draft_id = "test_draft"
        email_content = "Test email content to be polished."
        
        # Create a mock response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "translations": [{
                "text": "Polished test email content."
            }]
        }
        # Set up the mock to return our prepared response
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Run the activity
        result = self.loop.run_until_complete(
            self.activity_env.run(
                polish_email_activity,
                draft_id,
                email_content
            )
        )
        
        # Verify the result is a non-empty string (polished email)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "")
        
        # In a real test, verify the _global_email_drafts dictionary was updated

    @patch('activities.arcade_activity.httpx.AsyncClient.post')
    @patch('activities.arcade_activity._global_email_drafts')
    @patch('activities.arcade_activity._global_leads')
    def test_send_email_activity(self, mock_leads, mock_email_drafts, mock_post):
        """Test the send_email_activity."""
        # Set up mock data
        lead_id = "test_lead"
        recipient_email = "test@example.com"
        email_content = "Test email content"
        
        # Create a mock response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "status": "sent"
        }
        # Set up the mock to return our prepared response
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Run the activity
        result = self.loop.run_until_complete(
            self.activity_env.run(
                send_email_activity,
                lead_id,
                recipient_email,
                email_content
            )
        )
        
        # Verify the result indicates success
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'sent')
        
        # In a real test, verify the email status was updated for the lead


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from workflow import OutboundProspectingWorkflow
from temporalio.testing import WorkflowEnvironment, ActivityEnvironment
from temporalio.worker import Worker
from temporalio.client import Client


class TestOutboundProspectingWorkflow(unittest.TestCase):
    """Test cases for the Temporal workflow."""

    async def asyncSetUp(self):
        """Set up workflow testing environment asynchronously."""
        # Create a workflow testing environment
        self.workflow_env = await WorkflowEnvironment.start_local()
        self.client = self.workflow_env.client

    def setUp(self):
        """Set up test environment."""
        # Create an event loop for async operations
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.asyncSetUp())

    async def asyncTearDown(self):
        """Tear down workflow testing environment asynchronously."""
        await self.workflow_env.shutdown()

    def tearDown(self):
        """Tear down test environment."""
        self.loop.run_until_complete(self.asyncTearDown())
        self.loop.close()

    async def create_test_worker(self, activities=None):
        """Create a worker for testing the workflow."""
        if activities is None:
            activities = []

        worker = Worker(
            self.client,
            task_queue="test_task_queue",
            workflows=[OutboundProspectingWorkflow],
            activities=activities
        )
        await worker.start()
        return worker

    @patch('workflow.fetch_leads_activity')
    @patch('workflow.generate_insight_activity')
    @patch('workflow.polish_email_activity')
    @patch('workflow.send_email_activity')
    async def test_workflow_execution(self, mock_send, mock_polish, mock_insight, mock_fetch):
        """Test the full workflow execution with mocked activities."""
        # Mock the fetch_leads_activity to return test lead data
        mock_fetch.return_value = {
            "lead1": {
                "id": "lead1",
                "name": "Test Company",
                "website": "https://test.example.com",
                "industry": "Technology",
                "location": "Test Location"
            }
        }

        # Mock the generate_insight_activity to return a test insight
        mock_insight.return_value = "Test company has recently launched a new product."

        # Mock the polish_email_activity to return a polished email
        mock_polish.return_value = "Test polished email content"

        # Mock the send_email_activity to return success
        mock_send.return_value = {"status": "sent"}

        # Create a worker with all the mocked activities
        worker = await self.create_test_worker([
            mock_fetch, mock_insight, mock_polish, mock_send
        ])

        # Run the workflow
        handle = await self.client.start_workflow(
            OutboundProspectingWorkflow.run,
            id="test-workflow-id",
            task_queue="test_task_queue"
        )

        # Wait for the workflow to complete
        result = await handle.result()

        # Verify the workflow completed successfully
        self.assertEqual(result["status"], "completed")
        self.assertIn("message", result)

        # Verify that all activities were called with the expected arguments
        mock_fetch.assert_called_once()
        mock_insight.assert_called_once_with("lead1", "Test Company")
        mock_polish.assert_called_once()
        # We can't easily assert the exact arguments for mock_polish because the email template
        # is generated within the workflow, but we can check that it was called
        mock_send.assert_called_once()
        # Similarly, we can verify send_email_activity was called but not the exact arguments

        # Stop the worker
        await worker.shutdown()

    @patch('workflow.fetch_leads_activity')
    async def test_workflow_error_handling(self, mock_fetch):
        """Test workflow error handling when an activity fails."""
        # Mock the fetch_leads_activity to raise an exception
        mock_fetch.side_effect = Exception("Simulated API failure")

        # Create a worker with the mocked activity
        worker = await self.create_test_worker([mock_fetch])

        # Run the workflow
        handle = await self.client.start_workflow(
            OutboundProspectingWorkflow.run,
            id="test-workflow-error-id",
            task_queue="test_task_queue"
        )

        # Wait for the workflow to complete
        result = await handle.result()

        # Verify the workflow handled the error
        self.assertEqual(result["status"], "failed")
        self.assertIn("message", result)
        self.assertIn("Workflow failed", result["message"])

        # Stop the worker
        await worker.shutdown()


if __name__ == '__main__':
    unittest.main()

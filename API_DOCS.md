# Outbound Sales Prospector API Documentation

This document provides detailed information about the backend API endpoints for the Outbound Sales Prospector application.

## Base URL

All endpoints are relative to the base URL:
```
http://localhost:5000
```

## Authentication

No authentication is required for this hackathon demo.

## Endpoints

### 1. Start Workflow

Initiates the outbound prospecting workflow.

**URL**: `/start`

**Method**: `POST`

**Request Body**: None required

**Success Response**:
- **Code**: 200 OK
- **Content Example**:
  ```json
  {
    "status": "started",
    "workflow_id": "outbound-prospecting-workflow-1651234567"
  }
  ```

**Error Response**:
- **Code**: 500 Internal Server Error
- **Content Example**:
  ```json
  {
    "status": "error",
    "message": "Failed to start workflow: Temporal server not running"
  }
  ```

**Usage Example**:
```javascript
// Using fetch
fetch('http://localhost:5000/start', { method: 'POST' })
  .then(response => response.json())
  .then(data => console.log(data));

// Using axios
axios.post('http://localhost:5000/start')
  .then(response => console.log(response.data));
```

### 2. Get Workflow State

Returns the current state of the workflow, including all leads, their processing status, and detailed progress information.

**URL**: `/state`

**Method**: `GET`

**Success Response**:
- **Code**: 200 OK
- **Content Example**:
  ```json
  {
    "leads": [
      {
        "id": "lead1",
        "name": "Acme Corporation",
        "website": "https://acme.example.com",
        "industry": "Technology",
        "location": "San Francisco, CA",
        "insight": "Acme Corporation recently secured a $50M Series C funding round...",
        "email_content": "Subject: Quick question about Acme Corporation\n\nHi Acme Corporation,\n...",
        "status": "sent"
      },
      {
        "id": "lead2",
        "name": "Globex Industries",
        "website": "https://globex.example.com",
        "industry": "Manufacturing",
        "location": "Chicago, IL",
        "insight": "Globex Industries has developed a revolutionary sustainable manufacturing process...",
        "email_content": "Subject: Quick question about Globex Industries\n\nHi Globex Industries,\n...",
        "status": "pending"
      }
    ],
    "workflowStatus": "in_progress",
    "currentStage": "generating_insights",
    "stageProgress": {
      "fetching_leads": 100,
      "generating_insights": 60,
      "drafting_emails": 0,
      "polishing_emails": 0,
      "sending_emails": 0
    }
  }
  ```

**Stage Information**:

The workflow is divided into distinct stages, each representing a step in the sales prospecting process:

| Stage Name | Description | Progress Tracking |
|------------|-------------|-------------------|
| `fetching_leads` | Collecting lead data from Apify | 0-100% based on API call progress |
| `generating_insights` | Creating personalized insights with Perplexity | 0-100% based on percentage of leads with insights |
| `drafting_emails` | Creating personalized email drafts | 0-100% based on emails drafted |
| `polishing_emails` | Refining email content with DeepL | 0-100% based on emails polished |
| `sending_emails` | Delivering emails via Arcade.dev | 0-100% based on emails sent |

The `currentStage` field indicates which stage is currently active, and `stageProgress` contains the completion percentage for each stage.

**Usage Example**:
```javascript
// Using fetch
fetch('http://localhost:5000/state')
  .then(response => response.json())
  .then(data => console.log(data));

// Using axios
axios.get('http://localhost:5000/state')
  .then(response => console.log(response.data));
```

### 3. Reset Workflow

Resets the workflow state for a new run.

**URL**: `/reset`

**Method**: `POST`

**Request Body**: None required

**Success Response**:
- **Code**: 200 OK
- **Content Example**:
  ```json
  {
    "status": "reset"
  }
  ```

**Usage Example**:
```javascript
// Using fetch
fetch('http://localhost:5000/reset', { method: 'POST' })
  .then(response => response.json())
  .then(data => console.log(data));

// Using axios
axios.post('http://localhost:5000/reset')
  .then(response => console.log(response.data));
```

## Response Object Structures

### Lead Object

| Field           | Type   | Description                                                 |
|-----------------|--------|-------------------------------------------------------------|
| `id`            | String | Unique identifier for the lead                              |
| `name`          | String | Company name                                                |
| `website`       | String | Company website URL                                         |
| `industry`      | String | Industry or sector of the company                           |
| `location`      | String | Company location                                            |
| `insight`       | String | AI-generated insight about the company (null if not yet generated) |
| `email_content` | String | The content of the personalized email (empty if not yet drafted) |
| `status`        | String | Status of the email: "pending" or "sent"                    |

### Workflow Status

The `workflowStatus` field can have one of the following values:
- `"idle"`: Workflow has not started or was reset
- `"in_progress"`: Workflow is currently running
- `"completed"`: All leads have been processed and all emails have been sent

## Testing the API

You can use tools like [Postman](https://www.postman.com/) or [cURL](https://curl.se/) to test the API endpoints manually.

### cURL Examples

1. Start the workflow:
```bash
curl -X POST http://localhost:5000/start
```

2. Get the current state:
```bash
curl http://localhost:5000/state
```

3. Reset the workflow:
```bash
curl -X POST http://localhost:5000/reset
```

## Frontend Integration Tips

1. **Polling Strategy**: When the workflow is in progress, poll the `/state` endpoint every 1-2 seconds to get updates.

2. **Error Handling**: Add appropriate error handling for API calls, especially for network errors.

3. **Conditional Rendering**: Use the `workflowStatus` field to determine what to show in the UI.

4. **Loading States**: Show loading indicators during API calls and when waiting for the workflow to complete.

5. **CORS Considerations**: The Flask backend has CORS enabled, but if you encounter issues, ensure your frontend's origin is allowed.

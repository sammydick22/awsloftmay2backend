# ProspectAutopilot Backend

The backend for ProspectAutopilot, an AI-powered sales prospecting system that discovers potential leads, enriches them with relevant information, and generates personalized outreach emails.

## Overview

This Flask-based backend orchestrates an autonomous workflow that:

1. Discovers recently funded companies using Perplexity's Sonar API
2. Extracts detailed contact information using Apify's web scraping capabilities
3. Generates custom insights for each company using AI
4. Creates and refines personalized email content
5. Simulates sending emails through Arcade.dev

## Features

- **AI-Powered Discovery**: Finds high-potential prospects based on recent funding events
- **Autonomous Data Enrichment**: Combines data from multiple sources to create rich lead profiles
- **Personalized Insight Generation**: Creates unique, relevant talking points for each prospect
- **Intelligent Email Generation**: Drafts personalized, polished outreach emails
- **End-to-End Pipeline**: Handles the complete workflow from discovery to delivery

## Architecture

The backend uses a modular architecture organized around specialized activities:

- **`app.py`**: Main Flask application with API endpoints
- **`worker.py`**: Worker configuration for activity execution
- **`workflow.py`**: Workflow orchestration logic
- **`activities/`**: Individual activity implementations
  - `perplexity_discovery_activity.py`: Discovers potential companies
  - `apify_activity.py`: Enriches leads with company and contact data
  - `perplexity_activity.py`: Generates personalized insights
  - `deepl_activity.py`: Polishes email content
  - `arcade_activity.py`: Handles email delivery

## API Endpoints

- **POST `/start`**: Start the prospecting workflow
- **GET `/state`**: Get current workflow state and results
- **POST `/reset`**: Reset the workflow state

## Third-Party Integrations

The backend integrates with multiple AI and data services:

- **Perplexity Sonar**: AI-powered web search and insight generation
- **Apify**: Web scraping for company and contact information
- **DeepL**: Natural language processing for content enhancement
- **Arcade.dev**: Tool-calling API for email delivery

## Setup & Development

### Prerequisites

- Python 3.10+
- Flask
- Required API keys for: Perplexity, Apify, DeepL, and Arcade.dev

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up API keys in environment variables or in `apikeys.txt`

### Running Locally

Start the Flask server:
```bash
python app.py
```

The server will be available at http://localhost:8000.

### Running Tests

Run the test suite:
```bash
python run_tests.py
```

## Data Flow

1. **Company Discovery**:
   - Input: Search parameters for recently funded companies
   - Output: List of companies with basic information

2. **Lead Enrichment**:
   - Input: Companies from the discovery phase
   - Output: Enhanced leads with contact details and company information

3. **Insight Generation**:
   - Input: Enriched leads
   - Output: Same leads with added personalized insights

4. **Email Drafting & Polishing**:
   - Input: Leads with insights
   - Output: Personalized, polished email content for each lead

5. **Email Sending**:
   - Input: Leads with email content
   - Output: Delivery status for each email


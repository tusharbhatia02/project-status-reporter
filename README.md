# Automated Project Status Reporter

## Overview

This project implements an automated system that aggregates project status information from multiple sources (Trello, Gmail, Slack) and generates an insightful analysis using AI. The goal is to provide project managers, team leads, and stakeholders with regular, concise updates on project health, potential risks, and actionable items.

The system fetches data using direct API calls (Trello) and standard Python libraries (Gmail, Slack). It then uses a sophisticated AI agent, built with **LangChain** and powered by **Google Gemini**, to analyze the aggregated data. The agent framework is set up using the **Pica LangChain SDK (`pica-langchain`)**, enabling potential integration with Pica's connector tools via an authenticated `PicaClient`. In this implementation, the core analysis relies on the Gemini LLM, and the generated analysis is posted directly to a designated Slack channel using the standard Slack SDK.

A web frontend built with **Next.js**, **TypeScript**, and **Tailwind CSS** provides an interface to trigger report generation and view the raw data and the AI-generated analysis.

## Real-World Scenario

### Team Setup
- **Project Phoenix Team**
  - Sarah (Project Manager)
  - David (Technical Lead)

### Daily Workflow
1. **Automated Report Generation**
   - System automatically generates and posts analysis to #project-phoenix-updates at 8:00 AM
   - Aggregates data from Trello, Gmail, and Slack
   - AI agent analyzes the data and generates actionable insights

2. **Team Interaction**
   - Sarah (PM) immediately sees the summary, action items, and risks on Slack
   - She can quickly tag David in a thread: "@David Can you prioritize the DB task? Who has context on the blocker messages?"
   - David (Lead) sees clear priorities and responds promptly within Slack
   - Team stays efficiently informed without wading through raw data

### Key Benefits
- **Efficiency**: Delivers insights, not just data
- **Actionability**: Clear priorities and next steps
- **Focus**: Cuts through noise to highlight important information
- **Collaboration**: Triggers team interaction directly in their communication hub

## Features

* **Multi-Source Data Aggregation:** Fetches data from:
  * Trello (Board lists, card counts, overdue status via Python `requests`)
  * Gmail (Recent unread emails with label `project-updates` via Google API Client & OAuth)
  * Slack (Recent messages from a specific channel via Slack SDK)
* **Data Processing & Filtering:**
  * Filters Slack messages to remove noise (joins, bot posts)
  * Applies basic keyword tagging (e.g., `[BLOCKER?]`) to Slack messages
  * Constructs a formatted raw report string using Markdown
* **AI-Powered Analysis (LangChain + Gemini + Pica Setup):**
  * Utilizes a LangChain agent framework set up via `pica-langchain` (`PicaClient`, `create_pica_agent`)
  * Connects to the Pica platform using `PICA_SECRET` to make Pica Connectors potentially available to the agent
  * Employs Google's Gemini model (e.g., `gemini-1.5-flash-latest` via `langchain-google-genai`) as the agent's "brain" to analyze the raw report
  * Generates a structured analysis including:
    * Concise Summary
    * Potential Action Items
    * Identified Risks/Blockers
* **Direct Slack Notification:** Posts the formatted AI analysis directly to a configured Slack channel using the standard Slack SDK (`slack_sdk`)
* **Web Frontend:** Provides an interactive interface (Next.js/TypeScript/Tailwind) to:
  * Trigger report generation via an API call
  * Display loading/error states
  * Show the final AI analysis (rendered from Markdown)
  * Display the raw aggregated data in structured cards (Trello, Email, Slack)
  * Show the status of the direct Slack notification attempt
* **Modular Backend:** Uses FastAPI with a structured layout (api, config, schemas, services, agents, scripts)
* **Pica DSL Artifact:** Includes `status_reporter.pica` as the design specification for the report generation logic

## Tech Stack

* **Backend:**
  * Python 3.11+
  * FastAPI, Uvicorn
  * LangChain (Core framework)
  * `pica-langchain` (Pica SDK for agent setup)
  * `langchain-google-genai`, `google-generativeai` (Gemini LLM)
  * `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2` (Gmail API)
  * `slack_sdk` (Slack API interaction)
  * `requests` (HTTP calls for Trello)
  * `python-dotenv`, `pydantic-settings` (Config/Env management)
  * `beautifulsoup4` (HTML parsing - if used in email parser)
* **Frontend:**
  * Node.js / npm (or yarn)
  * Next.js (App Router)
  * TypeScript
  * Tailwind CSS (+ `@tailwindcss/typography`)
  * `axios` (HTTP client)
  * `react-markdown` (Markdown rendering)
* **External Services:**
  * Trello Account & Board
  * Google Cloud Project (Gmail API & Gemini API enabled)
  * Slack Workspace & App (Bot with specific scopes)
  * Pica Account (picaos.com) (for `PICA_SECRET`)
  * Google AI Studio (for Gemini API Key)

## Project Structure

```
project-status-reporter/
├── backend/
│   ├── agents/           # Agent/LLM logic
│   │   ├── __init__.py
│   │   └── analysis_agent.py
│   ├── api/             # FastAPI app, routes
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── report_router.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── config/          # Pydantic settings
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── schemas/         # Pydantic models
│   │   ├── __init__.py
│   │   └── report_schema.py
│   ├── services/        # Data fetching, report building, notifications
│   │   ├── __init__.py
│   │   ├── report_builder.py
│   │   ├── slack_service.py
│   │   ├── gmail_service.py
│   │   └── trello_service.py
│   ├── scripts/         # Setup scripts
│   │   └── gmail_auth.py
│   ├── venv/           # Python virtual environment (Gitignored)
│   ├── .env            # Environment variables (Gitignored)
│   ├── credentials.json # Gmail API credentials (Gitignored)
│   ├── requirements.txt # Python dependencies
│   ├── status_reporter.pica # Pica DSL design artifact
│   └── token.json      # Gmail OAuth token (Gitignored)
└── frontend/
    ├── app/            # Next.js App Router structure
    ├── components/     # React components
    ├── public/         # Static assets
    ├── styles/         # Global CSS, Tailwind
    ├── .env.local      # Frontend environment variables (Gitignored)
    ├── next.config.js  # Next.js config
    ├── package.json    # Node dependencies
    ├── tailwind.config.ts # Tailwind config
    └── tsconfig.json   # TypeScript config
```

## Setup and Running Locally

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd project-status-reporter
```

### 2. Backend Setup

#### a. Navigate to Backend
```bash
cd backend
```

#### b. Create & Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

#### c. Install Dependencies
```bash
pip install -r requirements.txt
```

#### d. Configure External Services & Get Credentials

##### Trello:
* Create a Trello board with lists
* Get your Trello API Key and Token (https://trello.com/app-key)
* Get your Trello Board ID from the board's URL

##### Google Cloud & Gmail API:
* In Google Cloud Console, enable the Gmail API
* Create OAuth 2.0 Credentials for a "Desktop app"
* Download the credentials.json file and place it in the backend directory

##### Google AI Studio & Gemini API:
* In Google Cloud Console, ensure the Vertex AI API (which hosts Gemini) or the direct Generative Language API is enabled
* Generate a Gemini API Key from Google AI Studio (https://aistudio.google.com/app/apikey) or Cloud Console

##### Slack:
* Create a Slack App (https://api.slack.com/apps)
* Add a Bot User
* Under "OAuth & Permissions" -> "Bot Token Scopes", add:
  * channels:history (to read messages)
  * users:read (to resolve user IDs)
  * chat:write (to post the analysis message)
* Install the app to your workspace and copy the Bot User OAuth Token (xoxb-...)
* Create a target Slack channel (e.g., #project-updates), invite your bot to it
* Get the Channel ID (C...) from the channel's URL

##### PicaOS:
* Sign up/log in at https://www.picaos.com/
* Get your Pica Secret Key (sk_test_... or sk_live_...)

#### e. Create and Populate .env File

Create a file named `.env` in the backend directory with your actual values:

```env
# Trello API Credentials
TRELLO_API_KEY=YOUR_TRELLO_API_KEY_HERE
TRELLO_TOKEN=YOUR_TRELLO_TOKEN_HERE
TRELLO_BOARD_ID=YOUR_TRELLO_BOARD_ID_HERE

# Slack API Credentials
SLACK_BOT_TOKEN=xoxb-YOUR_SLACK_BOT_TOKEN_HERE
SLACK_CHANNEL_ID=YOUR_SLACK_CHANNEL_ID_HERE

# Google Gemini API Key
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY_HERE

# Pica Secret Key
PICA_SECRET=sk_test_1_YOUR_PICA_SECRET_HERE

# Optional: Set log level (DEBUG, INFO, WARNING, ERROR)
# LOG_LEVEL=INFO
```

#### f. Run Gmail Authentication Script (One-Time Setup)
* Ensure credentials.json is in the backend directory
* Make sure scripts/gmail_auth.py requests the https://www.googleapis.com/auth/gmail.modify scope
* Run the script from the backend directory:
```bash
python scripts/gmail_auth.py
```
* Follow the browser prompts to log in and grant the requested permissions (including modify access)
* Verify token.json is created in the backend directory

#### g. Set up Gmail Label
In Gmail, create a label named project-updates. Label some test emails and ensure at least one is unread before your first test run.

### 3. Frontend Setup

#### a. Navigate to Frontend
```bash
cd ../frontend  # From backend directory
```

#### b. Install Dependencies
```bash
npm install  # or: yarn install
# Ensure @tailwindcss/typography is installed if using 'prose' classes
npm install -D @tailwindcss/typography
```

#### c. Create .env.local File
Create a file named `.env.local` in the frontend directory:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```
(Adjust if your backend runs on a different port)

#### d. Configure Tailwind
Ensure require('@tailwindcss/typography') is added to the plugins array in frontend/tailwind.config.ts

### 4. Running the Application

#### a. Start Backend Server
* Open a terminal in the backend directory
* Activate venv: `source venv/bin/activate`
* Run Uvicorn:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
* Keep this terminal running

#### b. Start Frontend Server
* Open a separate terminal in the frontend directory
* Run the Next.js dev server:
```bash
npm run dev  # or: yarn dev
```
* Keep this terminal running

#### c. Access Application
Open your web browser to http://localhost:3000

#### d. Generate Report
Click the "Generate Status Report" button. Observe the frontend UI update, check the backend logs for details, and check your Slack channel for the analysis message.

## How Pica Integration Works Here

### PicaClient
Uses the PICA_SECRET to connect to the Pica platform (api.picaos.com), authenticating and fetching definitions for potentially available Pica Connectors associated with your account.

### create_pica_agent
This pica-langchain function builds a LangChain agent framework (AgentExecutor) that is initialized with the PicaClient. This makes the agent aware of the Pica Connectors discovered by the client, enabling it to potentially use them as tools if prompted.

### Agent Execution
The agent uses the configured Gemini LLM (ChatGoogleGenerativeAI) for its core reasoning and analysis task based on the prompt and the raw report data provided by the Python services. In this specific workflow, the agent's analysis task does not require calling external Pica Connector tools, so it relies on the LLM's capabilities. The Pica integration provides the framework for potential tool use.


## Future Enhancements

* Modify the agent prompt to explicitly use authorized Pica Connectors (e.g., Notion, Jira, GitHub) for actions like archiving reports or creating tasks
* Implement direct Notion page creation using notion-client in Python as a separate notification step
* Refine Slack/Email filtering and keyword tagging in Python services
* Add date range parameters for data fetching
* Improve frontend UI/UX further
* Add comprehensive unit and integration tests 
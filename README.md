# 📧 Taskflow

A powerful Flask application that automatically converts Gmail emails into tasks using Google Tasks. Uses AI-powered classification to intelligently decide which emails should become tasks and automatically creates calendar events for meetings.

## ✨ Features

- **🔐 Secure Gmail Integration**: OAuth2 authentication with Google
- **⚡ Automatic Task Creation**: Convert emails to Google Tasks instantly
- **📅 Calendar Event Creation**: Automatically creates Google Calendar events for meeting invitations
- **🤖 AI-Powered Classification**: Machine learning to decide which emails should become tasks
- **✨ Smart Task Generation**: AI-generated task titles and descriptions from email content
- **🎯 Smart Email Processing**: Extract subject, sender, and body content (handles HTML emails)
- **📊 Flexible Search**: Process emails by time window, custom queries, or date ranges
- **🎨 Modern UI**: Clean, responsive interface inspired by Notion
- **👤 Multi-User Support**: User-specific data isolation with SQLite database
- **📱 Mobile Friendly**: Works seamlessly on all devices

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip3
- Google account with Gmail, Google Tasks, and Google Calendar access
- OpenAI API key (for AI-powered classification and task generation)
- Node.js and npm (for frontend development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd emailToTaskDev
   ```

2. **Make the setup script executable and run it**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   The setup script will:
   - Install all Python dependencies
   - Guide you through Google OAuth setup
   - Create environment variables

3. **Start the application**
   ```bash
   python3 server/app.py
   ```
   
   Or use npm scripts:
   ```bash
   npm run dev  # Runs both frontend and backend
   ```

4. **Open your browser**
   Navigate to `http://localhost:5001`

## 🔧 Manual Setup

If you prefer manual setup or the script doesn't work:

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Gmail API
   - Google Tasks API
   - Google Calendar API
4. Go to "Credentials" and create OAuth 2.0 Client ID
5. Set application type to "Web application"
6. Add `http://localhost:5173/oauth2callback` to authorized redirect URIs (this goes through the Vite proxy)
7. Download the JSON file and save it as `client_secret.json` in the project root

### 3. OpenAI API Setup

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (you won't be able to see it again)

### 5. Environment Configuration

Create a `.env` file:

```env
# Flask Configuration
FLASK_SECRET=your-secret-key-here
FLASK_ENV=development

# Google OAuth Configuration
GOOGLE_CLIENT_SECRETS=client_secret.json
GOOGLE_REDIRECT_URI=http://localhost:5173/oauth2callback

# Task Provider Configuration
DEFAULT_TASK_PROVIDER=google_tasks
TASKS_LIST_TITLE=Email Tasks

# OpenAI Configuration for ML Classification
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Application Configuration
FETCH_LIMIT=10
PORT=5001
FRONTEND_URL=http://localhost:5173
```

## 📖 How to Use

### 1. Connect Gmail

1. Open the application in your browser
2. Click "Connect with Google"
3. Authorize the application to access your Gmail

### 2. Process Emails

1. Go to the "Process Emails" tab
2. Configure your search parameters:
   - **Task Provider**: Choose Google Tasks (default)
   - **Max Emails**: Set how many emails to process at once (optional)
   - **Time Window**: Filter emails by date range (Last 24 hours, 7 days, 30 days, or all)
   - **Custom Query**: Use Gmail search syntax for advanced filtering (optional)
   - **Since Hours**: Filter emails from the last N hours (e.g., "24h", "1.5h", "90m")
   - **Since Date**: Filter emails from a specific ISO date (e.g., "2025-01-15T00:00:00Z")
   - **Dry Run**: Test without actually creating tasks
3. Click "Process Emails" to start processing

### 3. View Results

The application will:
- Show you the Gmail query used
- Display how many tasks and calendar events were created
- List all newly created tasks with links to Google Tasks
- List all newly created calendar events with links to Google Calendar
- Show statistics (total found, already processed, considered)

### 4. View All Tasks and Events

- **Tasks Tab**: View all tasks created from emails, sorted by creation date
- **Calendar Tab**: View all calendar events created from emails, sorted by creation date

## ⚙️ Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_SECRET` | Flask session secret key | `dev-change-me` |
| `FLASK_ENV` | Flask environment (development/production) | `development` |
| `GOOGLE_CLIENT_SECRETS` | Path to Google OAuth credentials | `client_secret.json` |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL | `http://localhost:5001/oauth2callback` |
| `DEFAULT_TASK_PROVIDER` | Default task provider | `google_tasks` |
| `TASKS_LIST_TITLE` | Title for the Google Tasks list | `Email Tasks` |
| `FETCH_LIMIT` | Maximum emails to process | `10` |
| `PORT` | Application port | `5001` |
| `FRONTEND_URL` | Frontend URL for OAuth redirects | `http://localhost:5173` |
| `OPENAI_API_KEY` | OpenAI API key for ML features | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` |
| `DB_DIR` | Directory for SQLite database | `/tmp` (Cloud Run) or local |

## 🤖 AI Classification Features

The application uses OpenAI's GPT models to intelligently process emails:

### Email Classification
The AI automatically determines whether an email should become a task based on:
- **Action items or requests** → Creates task
- **Reminders or deadlines** → Creates task
- **Meeting invitations** → Creates task + calendar event
- **Bills or payments** → Creates task
- **Pure newsletters** → Skips
- **Marketing content** → Skips
- **Social media notifications** → Skips
- **FYI-only messages** → Skips

### Meeting Detection
The AI automatically detects meeting invitations and:
- Creates a Google Calendar event with the meeting details
- Extracts meeting time, location, and participants
- Links the calendar event to the original email

### Task Generation
For emails classified as tasks, the AI:
- **Generates concise titles**: Actionable, 3-8 words, removing prefixes like "RE:", "FWD:"
- **Creates clean descriptions**: Extracts key details, dates, and requirements
- **Handles HTML content**: Automatically converts HTML emails to clean plain text
- **Provides reasoning**: Logs why decisions were made (visible in console)

### Fallback Behavior
If OpenAI API is unavailable or not configured:
- All emails are processed as tasks (default behavior)
- Original email subject becomes task title
- Original email body becomes task description


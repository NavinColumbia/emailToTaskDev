#!/bin/bash

# Email to Task Setup Script
# This script sets up the email-to-task application with all necessary dependencies and configuration

set -e  # Exit on any error

echo "🚀 Email to Task Setup Script"
echo "=============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is installed
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_success "Python $PYTHON_VERSION found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3."
    exit 1
fi

print_success "pip3 found"

# Install Python dependencies
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    print_success "Dependencies installed successfully"
else
    print_error "requirements.txt not found!"
    exit 1
fi

echo ""
print_status "Checking for Google OAuth client secret..."

# Check if client_secret.json exists
if [ ! -f "client_secret.json" ]; then
    print_warning "client_secret.json not found!"
    echo ""
    echo "To get your Google OAuth client secret:"
    echo "1. Go to https://console.developers.google.com/"
    echo "2. Create a new project or select an existing one"
    echo "3. Enable the Gmail API"
    echo "4. Go to 'Credentials' and create OAuth 2.0 Client ID"
    echo "5. Set application type to 'Web application'"
    echo "6. Add 'http://127.0.0.1:5000/oauth2callback' to authorized redirect URIs"
    echo "7. Download the JSON file and save it as 'client_secret.json' in this directory"
    echo ""
    
    # Ask for confirmation
    while true; do
        read -p "Have you added client_secret.json to this directory? (y/n): " yn
        case $yn in
            [Yy]* ) 
                if [ -f "client_secret.json" ]; then
                    print_success "client_secret.json found!"
                    break
                else
                    print_error "client_secret.json still not found. Please add it and run this script again."
                    exit 1
                fi
                ;;
            [Nn]* ) 
                print_error "Please add client_secret.json and run this script again."
                exit 1
                ;;
            * ) echo "Please answer yes (y) or no (n).";;
        esac
    done
else
    print_success "client_secret.json found!"
fi

echo ""
print_status "Setting up environment variables..."

# Get Todoist API token
echo ""
echo "To get your Todoist API token:"
echo "1. Go to https://todoist.com/prefs/integrations"
echo "2. Copy your API token"
echo ""

while true; do
    read -p "Enter your Todoist API token: " TODOIST_TOKEN
    if [ -n "$TODOIST_TOKEN" ]; then
        break
    else
        print_error "API token cannot be empty. Please enter a valid token."
    fi
done

# Create .env file with all environment variables
print_status "Creating .env file..."

cat > .env << EOF
# Flask Configuration
FLASK_SECRET=dev-change-me-$(date +%s)

# Google OAuth Configuration
GOOGLE_CLIENT_SECRETS=client_secret.json
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/oauth2callback

# Gmail Configuration
GMAIL_FORWARD_LABEL=todoist-forward
PROCESSED_STORE=processed.json

# Task Provider Configuration
DEFAULT_TASK_PROVIDER=todoist
TODOIST_API_TOKEN=$TODOIST_TOKEN

# Application Configuration
FETCH_LIMIT=10
PORT=5000
EOF

print_success ".env file created successfully"

echo ""
print_status "Setup Summary:"
echo "================"
echo "✅ Python dependencies installed"
echo "✅ Google OAuth client secret configured"
echo "✅ Todoist API token configured"
echo "✅ Environment variables saved to .env"
echo ""

print_success "Setup completed successfully! 🎉"
echo ""
echo "Next steps:"
echo "1. Run the application: python3 app.py"
echo "2. Open your browser to: http://127.0.0.1:5000"
echo "3. Authorize with Google to connect your Gmail"
echo "4. Start forwarding emails to create tasks!"
echo ""
echo "For more information, check the README or run: python3 app.py --help"

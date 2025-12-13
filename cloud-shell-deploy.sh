#!/bin/bash
# Cloud Shell Deployment Guide for Send to Kindle MCP Server
# Run this script in Google Cloud Shell

set -e

cat << 'BANNER'
╔═══════════════════════════════════════════════════════════╗
║   Send to Kindle MCP Server - Cloud Shell Deployment    ║
╔═══════════════════════════════════════════════════════════╗
BANNER

echo ""
echo "This script will guide you through deploying to Google Cloud Run."
echo "Make sure you have your email credentials ready:"
echo "  - SMTP host (e.g., smtp.gmail.com)"
echo "  - SMTP port (e.g., 587)"
echo "  - SMTP username (your email)"
echo "  - SMTP password (App Password for Gmail)"
echo "  - Kindle email address"
echo "  - Sender email address"
echo ""

# Step 1: Clone the repository if not already done
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Setting up repository"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "send-to-kindle-mcp" ]; then
    echo "Cloning repository..."
    git clone https://github.com/wahiggins3/send-to-kindle-mcp.git
    cd send-to-kindle-mcp
    git checkout claude/deploy-mcp-gcp-01D6vW3Wgj2y5zhgi7gcGpJo
else
    echo "Repository already exists, updating..."
    cd send-to-kindle-mcp
    git fetch origin
    git checkout claude/deploy-mcp-gcp-01D6vW3Wgj2y5zhgi7gcGpJo
    git pull
fi

echo "✓ Repository ready"
echo ""

# Step 2: Get GCP Project ID
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Setting up GCP Project"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$CURRENT_PROJECT" ]; then
    echo "No GCP project is currently set."
    echo ""
    echo "Available projects:"
    gcloud projects list
    echo ""
    echo "Enter your GCP Project ID:"
    read -r PROJECT_ID
else
    echo "Current project: $CURRENT_PROJECT"
    echo ""
    echo "Use this project? (y/n)"
    read -r USE_CURRENT
    if [[ "$USE_CURRENT" =~ ^[Yy]$ ]]; then
        PROJECT_ID="$CURRENT_PROJECT"
    else
        echo "Enter your GCP Project ID:"
        read -r PROJECT_ID
    fi
fi

export GCP_PROJECT_ID="$PROJECT_ID"
gcloud config set project "$PROJECT_ID"

echo "✓ Using project: $PROJECT_ID"
echo ""

# Step 3: Run the deployment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Running Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "The deployment script will now:"
echo "  1. Enable required GCP APIs"
echo "  2. Build your container image"
echo "  3. Prompt you for credentials (stored securely in Secret Manager)"
echo "  4. Deploy to Cloud Run"
echo ""
echo "Press Enter to continue..."
read -r

bash deploy.sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

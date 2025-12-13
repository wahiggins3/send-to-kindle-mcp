#!/bin/bash
# Deploy Send to Kindle MCP Server to Google Cloud Run

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="send-to-kindle-mcp"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Send to Kindle MCP Server - Cloud Run Deployment ===${NC}\n"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if project ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}GCP_PROJECT_ID not set. Please enter your GCP Project ID:${NC}"
    read -r PROJECT_ID
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}Error: Project ID is required${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Using GCP Project:${NC} $PROJECT_ID"
echo -e "${GREEN}Region:${NC} $REGION"
echo -e "${GREEN}Service Name:${NC} $SERVICE_NAME\n"

# Set the project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo -e "\n${YELLOW}Enabling required GCP APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    --quiet

# Build the container image
echo -e "\n${YELLOW}Building container image...${NC}"
gcloud builds submit --tag "$IMAGE_NAME" --quiet

# Check if secrets exist, if not create them
echo -e "\n${YELLOW}Checking secrets...${NC}"

create_secret_if_not_exists() {
    local secret_name=$1
    local secret_description=$2

    if ! gcloud secrets describe "$secret_name" &> /dev/null; then
        echo -e "${YELLOW}Creating secret: $secret_name${NC}"
        echo -e "${YELLOW}$secret_description${NC}"
        read -rs secret_value
        echo -n "$secret_value" | gcloud secrets create "$secret_name" \
            --data-file=- \
            --replication-policy="automatic" \
            --quiet
        echo -e "${GREEN}✓ Secret created${NC}"
    else
        echo -e "${GREEN}✓ Secret $secret_name already exists${NC}"
    fi
}

create_secret_if_not_exists "smtp-host" "Enter SMTP host (e.g., smtp.gmail.com):"
create_secret_if_not_exists "smtp-port" "Enter SMTP port (e.g., 587):"
create_secret_if_not_exists "smtp-user" "Enter SMTP username (your email):"
create_secret_if_not_exists "smtp-password" "Enter SMTP password (App Password for Gmail):"
create_secret_if_not_exists "kindle-email" "Enter your Kindle email address:"
create_secret_if_not_exists "from-email" "Enter sender email address:"

# Optional: Author name
if ! gcloud secrets describe "author-name" &> /dev/null; then
    echo -e "${YELLOW}Enter author name (optional, press Enter to skip):${NC}"
    read -r author_name
    if [ -n "$author_name" ]; then
        echo -n "$author_name" | gcloud secrets create "author-name" \
            --data-file=- \
            --replication-policy="automatic" \
            --quiet
        echo -e "${GREEN}✓ Author name secret created${NC}"
    fi
fi

# Deploy to Cloud Run
echo -e "\n${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --set-env-vars "MCP_TRANSPORT=http" \
    --set-secrets "SMTP_HOST=smtp-host:latest,SMTP_PORT=smtp-port:latest,SMTP_USER=smtp-user:latest,SMTP_PASSWORD=smtp-password:latest,KINDLE_EMAIL=kindle-email:latest,FROM_EMAIL=from-email:latest,AUTHOR_NAME=author-name:latest" \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)')

echo -e "\n${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Your MCP server is now running at:${NC}"
echo -e "${GREEN}$SERVICE_URL${NC}\n"

echo -e "${YELLOW}To use this server with AI tools, configure them to connect to:${NC}"
echo -e "${GREEN}${SERVICE_URL}/mcp${NC}\n"

echo -e "${YELLOW}To view logs:${NC}"
echo -e "gcloud run services logs read $SERVICE_NAME --region $REGION\n"

echo -e "${YELLOW}To update secrets:${NC}"
echo -e "gcloud secrets versions add <secret-name> --data-file=-\n"

echo -e "${YELLOW}To redeploy after code changes:${NC}"
echo -e "bash deploy.sh\n"

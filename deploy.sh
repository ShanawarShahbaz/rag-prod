#!/bin/bash

# Production Deployment Script for Google Cloud Run
# Usage: ./deploy.sh

set -e

echo "🚀 AI/LLM Job Application System - Production Deployment"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker Desktop${NC}"
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}✅ Docker installed${NC}"

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK${NC}"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo -e "${GREEN}✅ gcloud CLI installed${NC}"

# Check .env file
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "   Please create .env with: cp .env.example .env"
    exit 1
fi
echo -e "${GREEN}✅ .env file exists${NC}"

# Check Gmail credentials
if [ ! -f job_application_system/gmail_credentials.json ]; then
    echo -e "${YELLOW}⚠️  Gmail credentials not found${NC}"
    echo "   This is optional for first deployment"
    echo "   You can add it later: job_application_system/gmail_credentials.json"
fi

# Get configuration
echo ""
echo -e "${BLUE}📝 Getting configuration...${NC}"

# Read from .env
JSEARCH_API_KEY=$(grep JSEARCH_API_KEY .env | cut -d= -f2 | tr -d ' ')
if [ -z "$JSEARCH_API_KEY" ]; then
    echo -e "${RED}❌ JSEARCH_API_KEY not set in .env${NC}"
    exit 1
fi
echo -e "${GREEN}✅ JSearch API Key configured${NC}"

# Get Google Cloud project ID
echo ""
echo -e "${BLUE}🔐 Getting Google Cloud configuration...${NC}"

PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No Google Cloud project configured${NC}"
    echo "   Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi
echo -e "${GREEN}✅ Project ID: $PROJECT_ID${NC}"

# Confirm deployment
echo ""
echo -e "${YELLOW}⚠️  DEPLOYMENT CONFIGURATION:${NC}"
echo "   Project ID: $PROJECT_ID"
echo "   Service: job-applications"
echo "   Region: us-central1"
echo "   Memory: 512Mi"
echo "   Timeout: 3600s"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

# Build and deploy
echo ""
echo -e "${BLUE}🐳 Building Docker image...${NC}"

gcloud run deploy job-applications \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 3600s \
  --set-env-vars JSEARCH_API_KEY=$JSEARCH_API_KEY,GMAIL_ENABLED=true \
  --project=$PROJECT_ID

# Get the service URL
echo ""
echo -e "${BLUE}🌐 Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe job-applications \
  --platform managed \
  --region us-central1 \
  --project=$PROJECT_ID \
  --format='value(status.url)')

echo -e "${GREEN}✅ Service URL: $SERVICE_URL${NC}"

# Test the deployment
echo ""
echo -e "${BLUE}🧪 Testing deployment...${NC}"
sleep 5  # Wait for service to be ready

TEST_RESULT=$(curl -s -w "\n%{http_code}" "$SERVICE_URL/health" || echo "error")
HTTP_CODE=$(echo "$TEST_RESULT" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Health check returned: $HTTP_CODE${NC}"
fi

# Create Cloud Scheduler job
echo ""
echo -e "${BLUE}📅 Setting up Cloud Scheduler...${NC}"

# Extract hour and minute from SCHEDULE_TIME
SCHEDULE_TIME=$(grep SCHEDULE_TIME .env | cut -d= -f2 | tr -d ' ' || echo "07:00")
HOUR=$(echo $SCHEDULE_TIME | cut -d: -f1)
MINUTE=$(echo $SCHEDULE_TIME | cut -d: -f2)

# Convert to UTC (KSA is UTC+3, so subtract 3 hours)
UTC_HOUR=$((HOUR - 3))
if [ $UTC_HOUR -lt 0 ]; then
    UTC_HOUR=$((UTC_HOUR + 24))
fi

CRON_EXPRESSION="$MINUTE $UTC_HOUR * * *"

echo "Creating scheduler job:"
echo "  Cron: $CRON_EXPRESSION"
echo "  Description: 'Daily job application cycle at $SCHEDULE_TIME KSA'"

# Check if job exists
if gcloud scheduler jobs describe job-applications-daily --location=us-central1 &>/dev/null; then
    echo "Updating existing scheduler job..."
    gcloud scheduler jobs update http job-applications-daily \
      --location=us-central1 \
      --schedule="$CRON_EXPRESSION" \
      --http-method=POST \
      --uri="$SERVICE_URL/run" \
      --oidc-service-account-email="cloud-scheduler@$PROJECT_ID.iam.gserviceaccount.com" \
      --project=$PROJECT_ID
else
    echo "Creating new scheduler job..."
    gcloud scheduler jobs create http job-applications-daily \
      --location=us-central1 \
      --schedule="$CRON_EXPRESSION" \
      --http-method=POST \
      --uri="$SERVICE_URL/run" \
      --oidc-service-account-email="cloud-scheduler@$PROJECT_ID.iam.gserviceaccount.com" \
      --project=$PROJECT_ID
fi

echo -e "${GREEN}✅ Cloud Scheduler configured${NC}"

# Display summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Service Details:"
echo "  URL: $SERVICE_URL"
echo "  Project: $PROJECT_ID"
echo "  Region: us-central1"
echo ""
echo "Scheduler Details:"
echo "  Name: job-applications-daily"
echo "  Schedule: $SCHEDULE_TIME KSA ($CRON_EXPRESSION UTC)"
echo "  Frequency: Daily"
echo ""
echo "Next Steps:"
echo "  1. Verify in Google Cloud Console:"
echo "     - Cloud Run: https://console.cloud.google.com/run"
echo "     - Cloud Scheduler: https://console.cloud.google.com/cloudscheduler"
echo ""
echo "  2. Force run immediately (optional):"
echo "     curl -X POST $SERVICE_URL/run"
echo ""
echo "  3. View logs:"
echo "     gcloud run logs read job-applications --follow --limit=50"
echo ""
echo "  4. Check application tracking:"
echo "     cat cv-and-applications/applications_tracking.csv"
echo ""
echo -e "${YELLOW}ℹ️  System will apply to 15 jobs daily at $SCHEDULE_TIME KSA${NC}"
echo -e "${YELLOW}Expected results in 30 days: ~3 job offers${NC}"
echo ""

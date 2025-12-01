#!/bin/bash

# Google Cloud Function Deployment Script for GWS User Sync (Scheduled)

set -e

# Configuration
FUNCTION_NAME="gws-user-sync"
REGION="us-central1"
RUNTIME="go121"
MEMORY="512MB"
TIMEOUT="540s"
ENTRY_POINT="SyncFlipsideCryptoUsersAndGroups"
TOPIC_NAME="gws-user-sync-trigger"
SCHEDULE_NAME="gws-user-sync-schedule"
SCHEDULE_CRON="0 9 * * 1-5"  # Run at 9 AM UTC, Monday through Friday
SCHEDULE_TIMEZONE="UTC"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Error: No active gcloud authentication found. Please run 'gcloud auth login' first."
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "Error: No default project set. Please run 'gcloud config set project YOUR_PROJECT_ID' first."
    exit 1
fi

echo "Deploying scheduled Google Cloud Function..."
echo "Project: $PROJECT_ID"
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Runtime: $RUNTIME"
echo "Schedule: $SCHEDULE_CRON ($SCHEDULE_TIMEZONE)"
echo ""

# Create Pub/Sub topic if it doesn't exist
echo "Creating Pub/Sub topic: $TOPIC_NAME"
gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID || echo "Topic already exists"

# Deploy the function with Pub/Sub trigger
echo "Deploying Cloud Function..."
gcloud functions deploy $FUNCTION_NAME \
    --runtime=$RUNTIME \
    --trigger-topic=$TOPIC_NAME \
    --entry-point=$ENTRY_POINT \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --region=$REGION \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    --source=.

# Create Cloud Scheduler job
echo "Creating Cloud Scheduler job: $SCHEDULE_NAME"
gcloud scheduler jobs create pubsub $SCHEDULE_NAME \
    --schedule="$SCHEDULE_CRON" \
    --topic=$TOPIC_NAME \
    --message-body='{"trigger":"scheduled"}' \
    --time-zone=$SCHEDULE_TIMEZONE \
    --project=$PROJECT_ID || echo "Scheduler job already exists, updating..."

# If job already exists, update it
if [ $? -ne 0 ]; then
    echo "Updating existing scheduler job..."
    gcloud scheduler jobs update pubsub $SCHEDULE_NAME \
        --schedule="$SCHEDULE_CRON" \
        --topic=$TOPIC_NAME \
        --message-body='{"trigger":"scheduled"}' \
        --time-zone=$SCHEDULE_TIMEZONE \
        --project=$PROJECT_ID
fi

echo ""
echo "Deployment completed successfully!"
echo ""
echo "Function details:"
gcloud functions describe $FUNCTION_NAME --region=$REGION --format="table(name,status,trigger.eventTrigger.eventType,trigger.eventTrigger.resource)"
echo ""
echo "Scheduler job details:"
gcloud scheduler jobs describe $SCHEDULE_NAME --format="table(name,schedule,timeZone,state)"
echo ""
echo "To manually trigger the function, you can use:"
echo "gcloud pubsub topics publish $TOPIC_NAME --message='{\"trigger\":\"manual\"}'"
echo ""
echo "To view function logs:"
echo "gcloud functions logs read $FUNCTION_NAME --region=$REGION"

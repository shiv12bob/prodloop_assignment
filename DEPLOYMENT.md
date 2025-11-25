# GCP Deployment Guide

This guide walks you through deploying the Prodloop Task Management API to Google Cloud Platform.

## Prerequisites

1. **Google Cloud Account** - with billing enabled
2. **gcloud CLI** - [Install guide](https://cloud.google.com/sdk/docs/install)
3. **Docker** - [Install guide](https://docs.docker.com/get-docker/)
4. **Git** - for repository management

## Step 1: Set Up GCP Project

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  pubsub.googleapis.com \
  cloudfunctions.googleapis.com \
  logging.googleapis.com
```

## Step 2: Create Pub/Sub Topic

```bash
# Create the Pub/Sub topic for task events
gcloud pubsub topics create task-events

# Create a subscription (optional, for testing)
gcloud pubsub subscriptions create task-events-sub --topic=task-events
```

## Step 3: Create Artifact Registry

```bash
# Create an Artifact Registry repository
gcloud artifacts repositories create prodloop \
  --repository-format=docker \
  --location=us-central1 \
  --description="Prodloop Task API Docker images"
```

## Step 4: Configure GitHub Secrets (for CI/CD)

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

```
GCP_PROJECT=<your-project-id>
GCP_REGION=us-central1
GCP_SA_KEY=<service-account-key-json>
ARTIFACT_REGISTRY_REPO=prodloop
CLOUD_RUN_SERVICE=task-api
PUBSUB_TOPIC=projects/<your-project-id>/topics/task-events
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
```

### Creating Service Account Key

```bash
# Create a service account
gcloud iam service-accounts create github-deploy \
  --display-name="GitHub Deployment Service"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member=serviceAccount:github-deploy@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/run.admin

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member=serviceAccount:github-deploy@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/artifactregistry.writer

# Generate and download the key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-deploy@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Use the contents of key.json for GCP_SA_KEY secret
```

## Step 5: Deploy Cloud Function

```bash
# Deploy the Pub/Sub subscriber as a Cloud Function
gcloud functions deploy task-subscriber \
  --runtime python311 \
  --trigger-topic task-events \
  --entry-point pubsub_handler \
  --source ./cloud_function \
  --set-env-vars "GEMINI_API_KEY=<your-gemini-api-key>,GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  --memory 256MB \
  --timeout 300s \
  --region us-central1
```

## Step 6: Deploy to Cloud Run (Manual)

```bash
# Build and push Docker image
gcloud builds submit --tag us-central1-docker.pkg.dev/$GCP_PROJECT_ID/prodloop/task-api

# Deploy to Cloud Run
gcloud run deploy task-api \
  --image us-central1-docker.pkg.dev/$GCP_PROJECT_ID/prodloop/task-api \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=$GCP_PROJECT_ID,PUBSUB_TOPIC=projects/$GCP_PROJECT_ID/topics/task-events,GEMINI_API_KEY=<your-gemini-api-key>" \
  --memory 512M \
  --timeout 300
```

## Step 7: Get the Cloud Run URL

```bash
gcloud run services describe task-api --region us-central1 --format='value(status.url)'
```

## Step 8: Test the API

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe task-api --region us-central1 --format='value(status.url)')

# Create a task
curl -X POST $SERVICE_URL/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Task","description":"This is a test","priority":"high"}'

# List tasks
curl $SERVICE_URL/tasks

# Health check
curl $SERVICE_URL/health
```

## Step 9: View Cloud Function Logs

```bash
# View logs from the Cloud Function
gcloud functions logs read task-subscriber --limit 50

# Or use Cloud Logging
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=task-subscriber" \
  --limit 50 \
  --format json
```

## Troubleshooting

### Cloud Function not triggered
- Check Pub/Sub topic exists: `gcloud pubsub topics list`
- Verify service account permissions for Cloud Function
- Check Cloud Function logs

### Gemini API errors
- Verify `GEMINI_API_KEY` is correctly set
- Check API quota at [Google Cloud Console](https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com)
- Test API key locally first

### Pub/Sub not publishing
- Verify topic path format: `projects/PROJECT_ID/topics/TOPIC_NAME`
- Check GCP credentials are available in environment
- Review application logs for publish errors

## Cleanup

```bash
# Delete Cloud Run service
gcloud run services delete task-api --region us-central1

# Delete Cloud Function
gcloud functions delete task-subscriber --region us-central1

# Delete Pub/Sub topic
gcloud pubsub topics delete task-events

# Delete Artifact Registry
gcloud artifacts repositories delete prodloop --location us-central1
```

## Next Steps

1. Set up GitHub Actions CI/CD by pushing code to main branch
2. Monitor Cloud Function logs for Gemini API responses
3. Scale Cloud Run service as needed
4. Set up monitoring and alerting in Cloud Logging

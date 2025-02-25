# Deploying Job Application Assistant to Google Cloud Platform

This guide provides step-by-step instructions for deploying the Job Application Assistant to Google Cloud Platform (GCP) using Cloud Run.

## Prerequisites

- Google Cloud Platform account
- Google Cloud SDK (gcloud CLI) installed and configured on your local machine
- Docker installed on your local machine
- GitHub account (for CI/CD setup)

## Windows-Specific Setup Instructions

If you're using Windows and encountering Python-related errors with the Google Cloud SDK, follow these steps:

### Fix Google Cloud SDK Python Issues on Windows

1. **Reinstall Google Cloud SDK with bundled Python**:
   - Uninstall your current Google Cloud SDK installation
   - Download the latest installer from: https://cloud.google.com/sdk/docs/install-sdk#windows
   - During installation, make sure to select the option to install bundled Python
   - After installation, open a new PowerShell or Command Prompt window (not Git Bash)

2. **Use PowerShell or Command Prompt instead of Git Bash**:
   - Google Cloud SDK works better with PowerShell or Command Prompt on Windows
   - Open PowerShell or Command Prompt
   - Navigate to your project directory:
     ```
     cd D:\path\to\Resume_answers_agent
     ```

3. **Use the PowerShell setup script**:
   ```powershell
   .\scripts\manual_gcp_setup.ps1
   ```
   
   This PowerShell script performs the same setup as the bash script but is designed to work better on Windows.

4. **If you still encounter issues**, follow the manual setup instructions below.

## Step 1: Set Up GCP Resources

### Initial Setup

1. Create a new GCP project or use an existing one
2. Enable the required APIs:
   - Cloud Run API
   - Artifact Registry API
   - Cloud Build API
   - Secret Manager API

You can use the provided setup script to automate this process:

```bash
chmod +x scripts/setup_gcp.sh
./scripts/setup_gcp.sh
```

The script will:
- Enable required APIs
- Create an Artifact Registry repository
- Create a service account for GitHub Actions
- Grant necessary permissions
- Create and download a service account key
- Store your Gemini API key in Secret Manager
- Output the values needed for GitHub secrets

### Manual Setup (If the script fails)

If the setup script fails, you can perform these steps manually:

1. **Create a new GCP project** (or use an existing one):
   ```bash
   gcloud projects create your-project-id --name="Resume Agent"
   gcloud config set project your-project-id
   ```

2. **Enable required APIs**:
   ```bash
   gcloud services enable artifactregistry.googleapis.com run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
   ```

3. **Create Artifact Registry repository**:
   ```bash
   gcloud artifacts repositories create resume-agent --repository-format=docker --location=us-central1 --description="Docker repository for Resume Agent"
   ```

4. **Create a service account for GitHub Actions**:
   ```bash
   gcloud iam service-accounts create github-actions --display-name="GitHub Actions"
   ```

5. **Grant necessary permissions**:
   ```bash
   gcloud projects add-iam-policy-binding your-project-id --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" --role="roles/artifactregistry.admin"
   
   gcloud projects add-iam-policy-binding your-project-id --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding your-project-id --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
   ```

6. **Create and download service account key**:
   ```bash
   gcloud iam service-accounts keys create ./gcp-key.json --iam-account=github-actions@your-project-id.iam.gserviceaccount.com
   ```

7. **Store Gemini API key in Secret Manager**:
   ```bash
   echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key --replication-policy="automatic" --data-file=-
   
   gcloud secrets add-iam-policy-binding gemini-api-key --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
   ```

8. **Get project number**:
   ```bash
   gcloud projects describe your-project-id --format="value(projectNumber)"
   ```

## Step 2: Manual Deployment

If you prefer to deploy manually without CI/CD:

### Build and Push Docker Images

1. Build the backend image:
```bash
docker build -t us-central1-docker.pkg.dev/your-project-id/resume-agent/resume-agent-backend:latest ./Backend
```

2. Build the frontend image:
```bash
docker build -t us-central1-docker.pkg.dev/your-project-id/resume-agent/resume-agent-frontend:latest ./Frontend/job_assistant
```

3. Authenticate with Artifact Registry:
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

4. Push the images:
```bash
docker push us-central1-docker.pkg.dev/your-project-id/resume-agent/resume-agent-backend:latest
docker push us-central1-docker.pkg.dev/your-project-id/resume-agent/resume-agent-frontend:latest
```

### Deploy to Cloud Run

1. Deploy the backend service:
```bash
gcloud run deploy resume-agent-backend \
  --image us-central1-docker.pkg.dev/your-project-id/resume-agent/resume-agent-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GEMINI_API_KEY=your-gemini-api-key"
```

2. Get the backend URL:
```bash
BACKEND_URL=$(gcloud run services describe resume-agent-backend --platform managed --region us-central1 --format="value(status.url)")
echo $BACKEND_URL
```

3. Deploy the frontend service:
```bash
gcloud run deploy resume-agent-frontend \
  --image us-central1-docker.pkg.dev/your-project-id/resume-agent/resume-agent-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="BACKEND_URL=$BACKEND_URL"
```

4. Get the frontend URL:
```bash
FRONTEND_URL=$(gcloud run services describe resume-agent-frontend --platform managed --region us-central1 --format="value(status.url)")
echo $FRONTEND_URL
```

## Step 3: Set Up CI/CD with GitHub Actions

1. Push your code to a GitHub repository

2. Add the following secrets to your GitHub repository:
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_PROJECT_NUMBER`: Your GCP project number
   - `GCP_REGION`: The GCP region (e.g., us-central1)
   - `GCP_SA_KEY`: The base64-encoded service account key
   - `GEMINI_API_KEY`: Your Google Gemini API key

3. Create the GitHub Actions workflow file:
   - The file is already created at `.github/workflows/deploy-gcp.yml`

4. Push to the main branch to trigger deployment

## Step 4: Set Up a Custom Domain (Optional)

1. Purchase a domain through Google Domains or another registrar

2. Map the domain to your Cloud Run services:
```bash
gcloud beta run domain-mappings create --service resume-agent-frontend --domain your-domain.com --region us-central1
```

3. Add the DNS records as instructed by the command output

4. For the backend, you can either:
   - Map a subdomain (e.g., api.your-domain.com) to the backend service
   - Use the default Cloud Run URL and update the frontend configuration

## Troubleshooting

### Container Fails to Start

1. Check the container logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=resume-agent-backend" --limit 50
```

2. Verify the environment variables are set correctly:
```bash
gcloud run services describe resume-agent-backend --platform managed --region us-central1
```

### Frontend Cannot Connect to Backend

1. Check that the BACKEND_URL environment variable is set correctly
2. Verify that the backend service is allowing unauthenticated access
3. Check the nginx configuration in the frontend container

### Permission Issues

1. Verify that the service account has the necessary permissions:
```bash
gcloud projects get-iam-policy your-project-id
```

2. Check that the Artifact Registry repository is accessible:
```bash
gcloud artifacts repositories list
```

### Windows-Specific Issues

1. **Python not found error**:
   - Reinstall Google Cloud SDK with bundled Python
   - Use PowerShell or Command Prompt instead of Git Bash
   - Set Python path for Google Cloud SDK:
     ```
     gcloud config set component_manager/python C:\Path\To\Python\python.exe
     ```

2. **Authentication issues**:
   - Run `gcloud auth login` in PowerShell or Command Prompt
   - Follow the browser authentication flow

## Maintenance

### Updating the Application

1. Make changes to your code
2. Push to the main branch to trigger automatic deployment
3. Or manually build and deploy:
```bash
docker build -t us-central1-docker.pkg.dev/your-project-id/resume-agent/resume-agent-backend:latest ./Backend
docker push us-central1-docker.pkg.dev/your-project-id/resume-agent/resume-agent-backend:latest
gcloud run deploy resume-agent-backend --image us-central1-docker.pkg.dev/your-project-id/resume-agent/resume-agent-backend:latest --platform managed --region us-central1
```

### Monitoring

1. View Cloud Run metrics:
```bash
gcloud run services describe resume-agent-backend --platform managed --region us-central1
```

2. Set up Cloud Monitoring alerts for:
   - Error rates
   - Latency
   - Container instance count

### Cost Management

Cloud Run charges based on:
- Number of requests
- Container instance time
- Memory allocation

To optimize costs:
1. Set appropriate memory limits
2. Configure concurrency settings
3. Set minimum instances to 0 for non-critical services
4. Monitor usage with Cloud Billing reports 

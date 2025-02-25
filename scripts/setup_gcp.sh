#!/bin/bash

# Exit on error
set -e

echo "=== Job Application Assistant GCP Setup ==="
echo "This script will set up Google Cloud Platform resources for deployment."
echo ""

# Check if running on Windows
if [[ "$(uname -s)" == *"MINGW"* ]] || [[ "$(uname -s)" == *"MSYS"* ]]; then
    echo "Detected Windows environment (Git Bash/MINGW)."
    echo "Note: There might be issues with gcloud in Git Bash on Windows."
    echo "If you encounter Python-related errors, please try running this script in PowerShell or Command Prompt instead."
    echo ""
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    echo ""
    echo "For Windows users:"
    echo "1. Download the installer from https://cloud.google.com/sdk/docs/install-sdk#windows"
    echo "2. Make sure to select the option to install bundled Python during installation"
    echo "3. After installation, open a new PowerShell or Command Prompt window and try again"
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "You are not logged in to Google Cloud. Please login first."
    echo ""
    echo "If you're on Windows and seeing Python-related errors, try these steps:"
    echo "1. Open PowerShell or Command Prompt as Administrator"
    echo "2. Run: gcloud auth login"
    echo "3. Follow the browser authentication flow"
    echo "4. Then run this script again"
    echo ""
    echo "Attempting to log in now..."
    
    # Try to login, but don't exit if it fails
    gcloud auth login || {
        echo ""
        echo "Login failed. Please try manually with these steps:"
        echo "1. Open PowerShell or Command Prompt (not Git Bash)"
        echo "2. Run: gcloud auth login"
        echo "3. After successful login, run this script again"
        exit 1
    }
fi

# Set default project
echo ""
read -p "Enter your GCP Project ID: " PROJECT_ID
gcloud config set project $PROJECT_ID || {
    echo "Failed to set project. Please try manually with:"
    echo "gcloud config set project $PROJECT_ID"
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable artifactregistry.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com || {
    echo "Failed to enable APIs. Please try manually with:"
    echo "gcloud services enable artifactregistry.googleapis.com run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com"
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

# Create Artifact Registry repository
echo "Creating Artifact Registry repository..."
gcloud artifacts repositories create resume-agent \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for Resume Agent" || {
    echo "Failed to create Artifact Registry repository. Please try manually with:"
    echo "gcloud artifacts repositories create resume-agent --repository-format=docker --location=us-central1 --description=\"Docker repository for Resume Agent\""
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

# Create a service account for GitHub Actions
echo "Creating service account for GitHub Actions..."
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions" || {
    echo "Failed to create service account. Please try manually with:"
    echo "gcloud iam service-accounts create github-actions --display-name=\"GitHub Actions\""
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

# Grant necessary permissions to the service account
echo "Granting permissions to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin" || {
    echo "Failed to grant artifactregistry.admin permission. Please try manually."
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin" || {
    echo "Failed to grant run.admin permission. Please try manually."
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" || {
    echo "Failed to grant iam.serviceAccountUser permission. Please try manually."
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

# Create and download service account key
echo "Creating service account key..."
gcloud iam service-accounts keys create ./gcp-key.json \
    --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com || {
    echo "Failed to create service account key. Please try manually with:"
    echo "gcloud iam service-accounts keys create ./gcp-key.json --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com"
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

# Store Gemini API key in Secret Manager
read -p "Enter your Gemini API key: " GEMINI_API_KEY
echo "Storing Gemini API key in Secret Manager..."
echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
    --replication-policy="automatic" \
    --data-file=- || {
    echo "Failed to store Gemini API key in Secret Manager. Please try manually."
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

# Grant access to the secret
gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" || {
    echo "Failed to grant access to the secret. Please try manually."
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)" 2>/dev/null) || {
    echo "Failed to get project number. Please check your project ID and try again."
    echo ""
    echo "Then continue with the manual setup steps in DEPLOYMENT-GCP.md"
    exit 1
}

echo ""
echo "Setup complete!"
echo "------------------------------------"
echo "Add the following secrets to your GitHub repository:"
echo "GCP_PROJECT_ID: $PROJECT_ID"
echo "GCP_PROJECT_NUMBER: $PROJECT_NUMBER"
echo "GCP_REGION: us-central1"
if [ -f "./gcp-key.json" ]; then
    echo "GCP_SA_KEY: $(cat ./gcp-key.json | base64 -w 0 2>/dev/null || cat ./gcp-key.json | base64)"
else
    echo "GCP_SA_KEY: [Service account key file not found]"
fi
echo "GEMINI_API_KEY: $GEMINI_API_KEY"
echo "------------------------------------"
echo "Important: Delete the gcp-key.json file after adding the secret to GitHub."
echo ""
echo "If you encountered any errors during this setup, please refer to DEPLOYMENT-GCP.md"
echo "for manual setup instructions." 
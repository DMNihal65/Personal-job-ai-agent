# PowerShell script for setting up GCP resources for Resume Agent
# This script is designed for Windows users who encounter issues with the bash script

Write-Host "=== Job Application Assistant GCP Setup (Windows) ===" -ForegroundColor Green
Write-Host "This script will set up Google Cloud Platform resources for deployment." -ForegroundColor Green
Write-Host ""

# Check if gcloud is installed
try {
    $gcloudVersion = gcloud --version
    Write-Host "Google Cloud SDK is installed." -ForegroundColor Green
} catch {
    Write-Host "ERROR: Google Cloud SDK (gcloud) is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install it from: https://cloud.google.com/sdk/docs/install-sdk#windows" -ForegroundColor Red
    Write-Host "Make sure to select the option to install bundled Python during installation." -ForegroundColor Red
    exit 1
}

# Check if user is logged in
try {
    $account = gcloud auth list --filter=status:ACTIVE --format="value(account)"
    if ([string]::IsNullOrEmpty($account)) {
        throw "No active account found"
    }
    Write-Host "Logged in as: $account" -ForegroundColor Green
} catch {
    Write-Host "You are not logged in to Google Cloud. Please login first." -ForegroundColor Yellow
    Write-Host "Attempting to log in now..." -ForegroundColor Yellow
    
    try {
        gcloud auth login
    } catch {
        Write-Host "Login failed. Please try again manually with: gcloud auth login" -ForegroundColor Red
        exit 1
    }
}

# Set default project
$PROJECT_ID = Read-Host -Prompt "Enter your GCP Project ID"
try {
    gcloud config set project $PROJECT_ID
    Write-Host "Project set to: $PROJECT_ID" -ForegroundColor Green
} catch {
    Write-Host "Failed to set project. Please try manually with: gcloud config set project $PROJECT_ID" -ForegroundColor Red
    Write-Host "Then continue with the manual setup steps in DEPLOYMENT-GCP.md" -ForegroundColor Red
    exit 1
}

# Enable required APIs
Write-Host "Enabling required APIs..." -ForegroundColor Yellow
try {
    gcloud services enable artifactregistry.googleapis.com run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
    Write-Host "APIs enabled successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to enable APIs. Please try manually with:" -ForegroundColor Red
    Write-Host "gcloud services enable artifactregistry.googleapis.com run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com" -ForegroundColor Red
    Write-Host "Then continue with the manual setup steps in DEPLOYMENT-GCP.md" -ForegroundColor Red
    exit 1
}

# Create Artifact Registry repository
Write-Host "Creating Artifact Registry repository..." -ForegroundColor Yellow
try {
    gcloud artifacts repositories create resume-agent --repository-format=docker --location=us-central1 --description="Docker repository for Resume Agent"
    Write-Host "Artifact Registry repository created successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to create Artifact Registry repository. Please try manually with:" -ForegroundColor Red
    Write-Host "gcloud artifacts repositories create resume-agent --repository-format=docker --location=us-central1 --description=""Docker repository for Resume Agent""" -ForegroundColor Red
    Write-Host "Then continue with the manual setup steps in DEPLOYMENT-GCP.md" -ForegroundColor Red
    exit 1
}

# Create a service account for GitHub Actions
Write-Host "Creating service account for GitHub Actions..." -ForegroundColor Yellow
try {
    gcloud iam service-accounts create github-actions --display-name="GitHub Actions"
    Write-Host "Service account created successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to create service account. Please try manually with:" -ForegroundColor Red
    Write-Host "gcloud iam service-accounts create github-actions --display-name=""GitHub Actions""" -ForegroundColor Red
    Write-Host "Then continue with the manual setup steps in DEPLOYMENT-GCP.md" -ForegroundColor Red
    exit 1
}

# Grant necessary permissions to the service account
Write-Host "Granting permissions to service account..." -ForegroundColor Yellow
try {
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/artifactregistry.admin"
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/run.admin"
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
    Write-Host "Permissions granted successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to grant permissions. Please try manually with the commands in DEPLOYMENT-GCP.md" -ForegroundColor Red
    Write-Host "Then continue with the manual setup steps in DEPLOYMENT-GCP.md" -ForegroundColor Red
    exit 1
}

# Create and download service account key
Write-Host "Creating service account key..." -ForegroundColor Yellow
try {
    gcloud iam service-accounts keys create ./gcp-key.json --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com
    Write-Host "Service account key created successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to create service account key. Please try manually with:" -ForegroundColor Red
    Write-Host "gcloud iam service-accounts keys create ./gcp-key.json --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com" -ForegroundColor Red
    Write-Host "Then continue with the manual setup steps in DEPLOYMENT-GCP.md" -ForegroundColor Red
    exit 1
}

# Store Gemini API key in Secret Manager
$GEMINI_API_KEY = Read-Host -Prompt "Enter your Gemini API key"
Write-Host "Storing Gemini API key in Secret Manager..." -ForegroundColor Yellow
try {
    $GEMINI_API_KEY | gcloud secrets create gemini-api-key --replication-policy="automatic" --data-file=-
    Write-Host "Gemini API key stored successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to store Gemini API key in Secret Manager. Please try manually." -ForegroundColor Red
    Write-Host "Then continue with the manual setup steps in DEPLOYMENT-GCP.md" -ForegroundColor Red
    exit 1
}

# Grant access to the secret
Write-Host "Granting access to the secret..." -ForegroundColor Yellow
try {
    gcloud secrets add-iam-policy-binding gemini-api-key --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
    Write-Host "Secret access granted successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to grant access to the secret. Please try manually." -ForegroundColor Red
    Write-Host "Then continue with the manual setup steps in DEPLOYMENT-GCP.md" -ForegroundColor Red
    exit 1
}

# Get project number
try {
    $PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
    Write-Host "Project number retrieved successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to get project number. Please check your project ID and try again." -ForegroundColor Red
    Write-Host "Then continue with the manual setup steps in DEPLOYMENT-GCP.md" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "------------------------------------" -ForegroundColor Green
Write-Host "Add the following secrets to your GitHub repository:" -ForegroundColor Yellow
Write-Host "GCP_PROJECT_ID: $PROJECT_ID" -ForegroundColor White
Write-Host "GCP_PROJECT_NUMBER: $PROJECT_NUMBER" -ForegroundColor White
Write-Host "GCP_REGION: us-central1" -ForegroundColor White

if (Test-Path "./gcp-key.json") {
    $keyContent = Get-Content -Path "./gcp-key.json" -Raw
    $encodedKey = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($keyContent))
    Write-Host "GCP_SA_KEY: $encodedKey" -ForegroundColor White
} else {
    Write-Host "GCP_SA_KEY: [Service account key file not found]" -ForegroundColor Red
}

Write-Host "GEMINI_API_KEY: $GEMINI_API_KEY" -ForegroundColor White
Write-Host "------------------------------------" -ForegroundColor Green
Write-Host "Important: Delete the gcp-key.json file after adding the secret to GitHub." -ForegroundColor Yellow
Write-Host ""
Write-Host "If you encountered any errors during this setup, please refer to DEPLOYMENT-GCP.md" -ForegroundColor Yellow
Write-Host "for manual setup instructions." -ForegroundColor Yellow 
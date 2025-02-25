@echo off
echo === Continuing GCP Setup ===

echo Adding IAM policy bindings...
gcloud projects add-iam-policy-binding savvy-webbing-452010-a3 --member="serviceAccount:github-actions@savvy-webbing-452010-a3.iam.gserviceaccount.com" --role="roles/artifactregistry.admin"
gcloud projects add-iam-policy-binding savvy-webbing-452010-a3 --member="serviceAccount:github-actions@savvy-webbing-452010-a3.iam.gserviceaccount.com" --role="roles/run.admin"
gcloud projects add-iam-policy-binding savvy-webbing-452010-a3 --member="serviceAccount:github-actions@savvy-webbing-452010-a3.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"

echo Creating service account key...
gcloud iam service-accounts keys create ./gcp-key.json --iam-account=github-actions@savvy-webbing-452010-a3.iam.gserviceaccount.com

echo Getting project number...
for /f "tokens=*" %%a in ('gcloud projects describe savvy-webbing-452010-a3 --format="value(projectNumber)"') do set PROJECT_NUMBER=%%a

echo.
echo Setup complete!
echo ------------------------------------
echo Add the following secrets to your GitHub repository:
echo GCP_PROJECT_ID: savvy-webbing-452010-a3
echo GCP_PROJECT_NUMBER: %PROJECT_NUMBER%
echo GCP_REGION: us-central1
echo GCP_SA_KEY: [Copy the contents of gcp-key.json and encode as base64]
echo ------------------------------------
echo Important: Delete the gcp-key.json file after adding the secret to GitHub.
echo.
echo For the GEMINI_API_KEY, you'll need to add that manually to GitHub secrets.

pause 
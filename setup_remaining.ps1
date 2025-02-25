Write-Host "=== Continuing GCP Setup ===" -ForegroundColor Green

Write-Host "Adding IAM policy bindings..." -ForegroundColor Yellow
& gcloud projects add-iam-policy-binding savvy-webbing-452010-a3 --member="serviceAccount:github-actions@savvy-webbing-452010-a3.iam.gserviceaccount.com" --role="roles/run.admin"
& gcloud projects add-iam-policy-binding savvy-webbing-452010-a3 --member="serviceAccount:github-actions@savvy-webbing-452010-a3.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"

Write-Host "Creating service account key..." -ForegroundColor Yellow
& gcloud iam service-accounts keys create ./gcp-key.json --iam-account=github-actions@savvy-webbing-452010-a3.iam.gserviceaccount.com

Write-Host "Getting project number..." -ForegroundColor Yellow
$PROJECT_NUMBER = & gcloud projects describe savvy-webbing-452010-a3 --format="value(projectNumber)"

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "------------------------------------" -ForegroundColor Cyan
Write-Host "Add the following secrets to your GitHub repository:" -ForegroundColor Yellow
Write-Host "GCP_PROJECT_ID: savvy-webbing-452010-a3"
Write-Host "GCP_PROJECT_NUMBER: $PROJECT_NUMBER"
Write-Host "GCP_REGION: us-central1"
Write-Host "GCP_SA_KEY: [Copy the contents of gcp-key.json and encode as base64]"
Write-Host "------------------------------------" -ForegroundColor Cyan
Write-Host "Important: Delete the gcp-key.json file after adding the secret to GitHub." -ForegroundColor Red
Write-Host ""
Write-Host "For the GEMINI_API_KEY, you'll need to add that manually to GitHub secrets." -ForegroundColor Yellow

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 
Write-Host "Adding necessary permissions to service account..." -ForegroundColor Green

$PROJECT_ID = "savvy-webbing-452010-a3"
$SERVICE_ACCOUNT = "github-actions@savvy-webbing-452010-a3.iam.gserviceaccount.com"

# List of roles to add
$roles = @(
    "roles/artifactregistry.admin",
    "roles/artifactregistry.writer",
    "roles/artifactregistry.reader",
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/storage.admin"
)

foreach ($role in $roles) {
    Write-Host "Adding role: $role" -ForegroundColor Yellow
    & gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICE_ACCOUNT" --role="$role"
}

Write-Host "All permissions added successfully!" -ForegroundColor Green 
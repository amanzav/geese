# Update Job Data Script
# Run this from the job-viewer directory after running the Python scraper

Write-Host "Updating job data files..." -ForegroundColor Green

$sourceDir = "..\data"
$targetDir = "public\data"

# Check if source files exist
if (!(Test-Path "$sourceDir\job_matches_cache.json")) {
    Write-Host "Error: job_matches_cache.json not found in $sourceDir" -ForegroundColor Red
    exit 1
}

if (!(Test-Path "$sourceDir\jobs_scraped.json")) {
    Write-Host "Error: jobs_scraped.json not found in $sourceDir" -ForegroundColor Red
    exit 1
}

# Create target directory if it doesn't exist
if (!(Test-Path $targetDir)) {
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
}

# Copy files
Copy-Item "$sourceDir\job_matches_cache.json" "$targetDir\job_matches_cache.json" -Force
Copy-Item "$sourceDir\jobs_scraped.json" "$targetDir\jobs_scraped.json" -Force

Write-Host "✓ Successfully updated job data files!" -ForegroundColor Green
Write-Host "Refresh your browser to see the updates." -ForegroundColor Cyan

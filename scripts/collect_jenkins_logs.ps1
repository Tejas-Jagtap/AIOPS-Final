# Jenkins Log Collection Script for AIOps
# This script collects Jenkins build logs and metadata for training the AIOps failure prediction model

param(
    [string]$JenkinsUrl = "http://localhost:8080",
    [string]$JobName = "aiops-demo-todo-app",
    [string]$Username = "admin",
    [string]$ApiToken = "",  # Set via -ApiToken flag or JENKINS_TOKEN env var
    [int]$MaxBuilds = 30,
    [string]$OutputDir = "data\jenkins_logs"
)

# Fall back to env var if no token provided
if ([string]::IsNullOrEmpty($ApiToken)) {
    $ApiToken = $env:JENKINS_TOKEN
}

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

Write-Host "========================================" -ForegroundColor $InfoColor
Write-Host "Jenkins Log Collection Script" -ForegroundColor $InfoColor
Write-Host "========================================" -ForegroundColor $InfoColor
Write-Host ""

# Check if API token is provided
if ([string]::IsNullOrEmpty($ApiToken)) {
    Write-Host "ERROR: Jenkins API Token is required!" -ForegroundColor $ErrorColor
    Write-Host ""
    Write-Host "To get your API token:" -ForegroundColor $WarningColor
    Write-Host "1. Login to Jenkins" -ForegroundColor $WarningColor
    Write-Host "2. Click your username (top right)" -ForegroundColor $WarningColor
    Write-Host "3. Click Configure" -ForegroundColor $WarningColor
    Write-Host "4. Scroll to API Token section" -ForegroundColor $WarningColor
    Write-Host "5. Click Add new Token and copy it" -ForegroundColor $WarningColor
    exit 1
}

# Create output directory
try {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    Write-Host "Output directory: $OutputDir" -ForegroundColor $SuccessColor
}
catch {
    Write-Host "ERROR: Failed to create output directory: $_" -ForegroundColor $ErrorColor
    exit 1
}

# Setup authentication
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${ApiToken}"))
$headers = @{ 
    Authorization = "Basic $auth"
    Accept        = "application/json"
}

Write-Host "Jenkins URL: $JenkinsUrl" -ForegroundColor $SuccessColor
Write-Host "Job Name: $JobName" -ForegroundColor $SuccessColor
Write-Host "Max Builds: $MaxBuilds" -ForegroundColor $SuccessColor
Write-Host ""

# Test Jenkins connection
Write-Host "Testing Jenkins connection..." -ForegroundColor $InfoColor
try {
    $testUrl = "$JenkinsUrl/api/json"
    $testResponse = Invoke-RestMethod -Uri $testUrl -Headers $headers -ErrorAction Stop
    Write-Host "Successfully connected to Jenkins" -ForegroundColor $SuccessColor
}
catch {
    Write-Host "ERROR: Failed to connect to Jenkins" -ForegroundColor $ErrorColor
    Write-Host "Error: $_" -ForegroundColor $ErrorColor
    Write-Host ""
    Write-Host "Please check:" -ForegroundColor $WarningColor
    Write-Host "  - Jenkins is running at $JenkinsUrl" -ForegroundColor $WarningColor
    Write-Host "  - API token is correct" -ForegroundColor $WarningColor
    Write-Host "  - Username is correct" -ForegroundColor $WarningColor
    exit 1
}

Write-Host ""
Write-Host "Fetching job information..." -ForegroundColor $InfoColor

# Get job information
try {
    $jobUrl = "$JenkinsUrl/job/$JobName/api/json?tree=builds[number,result,timestamp,duration,url]"
    $jobInfo = Invoke-RestMethod -Uri $jobUrl -Headers $headers -ErrorAction Stop
    
    if ($null -eq $jobInfo.builds -or $jobInfo.builds.Count -eq 0) {
        Write-Host "WARNING: No builds found for job" -ForegroundColor $WarningColor
        Write-Host "Please run at least one build before collecting logs." -ForegroundColor $WarningColor
        exit 0
    }
    
    $totalBuilds = $jobInfo.builds.Count
    Write-Host "Found $totalBuilds builds" -ForegroundColor $SuccessColor
}
catch {
    Write-Host "ERROR: Failed to fetch job information" -ForegroundColor $ErrorColor
    Write-Host "Error: $_" -ForegroundColor $ErrorColor
    exit 1
}

Write-Host ""
Write-Host "Downloading build logs..." -ForegroundColor $InfoColor
Write-Host "========================================" -ForegroundColor $InfoColor

# Statistics
$successCount = 0
$failedCount = 0

# Download logs for recent builds
$buildsToProcess = $jobInfo.builds | Select-Object -First $MaxBuilds

foreach ($build in $buildsToProcess) {
    $buildNum = $build.number
    $result = $build.result
    $timestamp = $build.timestamp
    $duration = $build.duration
    $url = $build.url
    
    # Convert timestamp (milliseconds since epoch)
    $buildDate = [DateTimeOffset]::FromUnixTimeMilliseconds($timestamp).DateTime
    $dateStr = $buildDate.ToString("yyyy-MM-dd_HHmmss")
    
    # Build result display
    $resultColor = switch ($result) {
        "SUCCESS" { $SuccessColor }
        "FAILURE" { $ErrorColor }
        "UNSTABLE" { $WarningColor }
        "ABORTED" { $WarningColor }
        default { $InfoColor }
    }
    
    Write-Host "Build #$buildNum - $result - $buildDate" -ForegroundColor $resultColor
    
    try {
        # Download console log
        $logUrl = "$JenkinsUrl/job/$JobName/$buildNum/consoleText"
        $logFile = Join-Path $OutputDir "build_${buildNum}_${dateStr}_${result}.log"
        
        Invoke-WebRequest -Uri $logUrl -Headers $headers -OutFile $logFile -ErrorAction Stop
        
        # Create metadata file
        $metadata = @{
            build_number     = $buildNum
            result           = $result
            timestamp        = $timestamp
            build_date       = $buildDate.ToString("o")
            duration_ms      = $duration
            duration_seconds = [math]::Round($duration / 1000, 2)
            url              = $url
            log_file         = Split-Path $logFile -Leaf
            collected_at     = (Get-Date).ToString("o")
        }
        
        $metadataFile = "$logFile.meta.json"
        $metadata | ConvertTo-Json -Depth 10 | Out-File -FilePath $metadataFile -Encoding UTF8
        
        # Get log file size
        $logSize = (Get-Item $logFile).Length
        $logSizeKB = [math]::Round($logSize / 1KB, 2)
        
        Write-Host "  Downloaded: $logSizeKB KB" -ForegroundColor $SuccessColor
        $successCount++
    }
    catch {
        Write-Host "  Failed to download: $_" -ForegroundColor $ErrorColor
        $failedCount++
    }
}

Write-Host "========================================" -ForegroundColor $InfoColor
Write-Host ""
Write-Host "Collection Summary:" -ForegroundColor $InfoColor
Write-Host "  Total builds processed: $($buildsToProcess.Count)" -ForegroundColor $InfoColor
Write-Host "  Successfully downloaded: $successCount" -ForegroundColor $SuccessColor
Write-Host "  Failed: $failedCount" -ForegroundColor $InfoColor
Write-Host ""

# Count builds by result
$resultCounts = $buildsToProcess | Group-Object -Property result

Write-Host "Build Results Distribution:" -ForegroundColor $InfoColor
foreach ($group in $resultCounts) {
    $color = switch ($group.Name) {
        "SUCCESS" { $SuccessColor }
        "FAILURE" { $ErrorColor }
        "UNSTABLE" { $WarningColor }
        default { $InfoColor }
    }
    Write-Host "  $($group.Name): $($group.Count)" -ForegroundColor $color
}

Write-Host ""
Write-Host "Logs saved to: $OutputDir" -ForegroundColor $SuccessColor
Write-Host ""

# Create summary file
$summaryData = @{
    collection_date      = (Get-Date).ToString("o")
    jenkins_url          = $JenkinsUrl
    job_name             = $JobName
    total_builds         = $buildsToProcess.Count
    successful_downloads = $successCount
    failed_downloads     = $failedCount
    output_directory     = $OutputDir
}

$summaryFile = Join-Path $OutputDir "collection_summary.json"
$summaryData | ConvertTo-Json -Depth 10 | Out-File -FilePath $summaryFile -Encoding UTF8
Write-Host "Summary saved to: $summaryFile" -ForegroundColor $InfoColor

Write-Host ""
Write-Host "========================================" -ForegroundColor $InfoColor
Write-Host "Collection Complete!" -ForegroundColor $SuccessColor
Write-Host "========================================" -ForegroundColor $InfoColor

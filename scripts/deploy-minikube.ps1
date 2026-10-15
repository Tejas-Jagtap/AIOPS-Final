<#
.SYNOPSIS
    Deploy AIOps system to Minikube for demo/testing.

.DESCRIPTION
    This script:
    1. Verifies Minikube is running
    2. Builds the orchestrator Docker image inside Minikube
    3. Deploys the demo app and orchestrator to Kubernetes
    4. Verifies all pods are running
    5. Outputs access URLs

.EXAMPLE
    .\scripts\deploy-minikube.ps1
#>

param(
    [switch]$SkipBuild,
    [switch]$CleanFirst
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " AIOps Minikube Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Check Minikube status
Write-Host "`n[1/6] Checking Minikube status..." -ForegroundColor Yellow
$minikubeStatus = minikube status --format "{{.Host}}" 2>$null
if ($minikubeStatus -ne "Running") {
    Write-Host "  Minikube not running. Starting..." -ForegroundColor Yellow
    minikube start --driver=docker --memory=4096 --cpus=2
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to start Minikube" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  Minikube is running" -ForegroundColor Green

# 2. Configure Docker environment to use Minikube's Docker daemon
Write-Host "`n[2/6] Configuring Docker environment..." -ForegroundColor Yellow
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
Write-Host "  Docker configured for Minikube" -ForegroundColor Green

# 3. Build Docker image
if (-not $SkipBuild) {
    Write-Host "`n[3/6] Building orchestrator Docker image..." -ForegroundColor Yellow
    Push-Location $PSScriptRoot\..
    docker build -t aiops-orchestrator:latest -f Dockerfile .
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Host "  ERROR: Docker build failed" -ForegroundColor Red
        exit 1
    }
    Pop-Location
    Write-Host "  Image built: aiops-orchestrator:latest" -ForegroundColor Green
}
else {
    Write-Host "`n[3/6] Skipping Docker build (--SkipBuild)" -ForegroundColor Yellow
}

# 4. Clean existing deployments if requested
if ($CleanFirst) {
    Write-Host "`n[4/6] Cleaning existing deployments..." -ForegroundColor Yellow
    kubectl delete -f "$PSScriptRoot\..\kubernetes_manifests\" --ignore-not-found 2>$null
    Start-Sleep -Seconds 5
    Write-Host "  Cleaned" -ForegroundColor Green
}
else {
    Write-Host "`n[4/6] Skipping clean (use -CleanFirst to clean)" -ForegroundColor Yellow
}

# 5. Deploy to Kubernetes
Write-Host "`n[5/6] Deploying to Kubernetes..." -ForegroundColor Yellow
$manifestDir = "$PSScriptRoot\..\kubernetes_manifests"

# Apply RBAC and service account first
kubectl apply -f "$manifestDir\orchestrator-deployment.yaml"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to deploy orchestrator" -ForegroundColor Red
    exit 1
}
Write-Host "  Orchestrator deployed" -ForegroundColor Green

# Apply services
kubectl apply -f "$manifestDir\service.yaml"
Write-Host "  Services created" -ForegroundColor Green

# Apply demo app
kubectl apply -f "$manifestDir\demo-app-deployment.yaml"
Write-Host "  Demo app deployed" -ForegroundColor Green

# Apply autoscaler
kubectl apply -f "$manifestDir\autoscaler-deployment.yaml"
Write-Host "  Autoscaler deployed" -ForegroundColor Green

# 6. Wait for pods to be ready
Write-Host "`n[6/6] Waiting for pods to be ready..." -ForegroundColor Yellow
$timeout = 120
$elapsed = 0
while ($elapsed -lt $timeout) {
    $pods = kubectl get pods --no-headers 2>$null
    $allReady = $true
    foreach ($line in $pods -split "`n") {
        if ($line -match "\d+/\d+") {
            $parts = $line -split "\s+"
            $ready = $parts[1]
            $status = $parts[2]
            if ($status -ne "Running" -and $status -ne "Completed") {
                $allReady = $false
            }
        }
    }
    
    if ($allReady -and $pods) {
        break
    }
    
    Write-Host "  Waiting... ($elapsed/$timeout s)" -ForegroundColor Gray
    Start-Sleep -Seconds 10
    $elapsed += 10
}

# Final status
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Deployment Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

kubectl get pods -o wide
kubectl get services

# Get access URL
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Access URLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$orchestratorUrl = minikube service aiops-orchestrator-lb --url 2>$null
if ($orchestratorUrl) {
    Write-Host "  Orchestrator: $orchestratorUrl" -ForegroundColor Green
}
else {
    Write-Host "  Orchestrator: kubectl port-forward svc/aiops-orchestrator 8000:8000" -ForegroundColor Yellow
}

$demoAppUrl = minikube service demo-todo-app --url 2>$null
if ($demoAppUrl) {
    Write-Host "  Demo App: $demoAppUrl" -ForegroundColor Green
}
else {
    Write-Host "  Demo App: kubectl port-forward svc/demo-todo-app 3000:3000" -ForegroundColor Yellow
}

Write-Host "`nDeployment complete!" -ForegroundColor Green

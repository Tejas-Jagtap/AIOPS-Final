# AIOps Demo Todo App - Jenkins Pipeline Testing

> **Purpose**: This is a demo Next.js application designed specifically for **Jenkins pipeline testing and log collection** for the AIOps system. It's NOT part of the main AIOps application but serves as a data source for generating CI/CD build logs, test results, and failure scenarios.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Jenkins Setup](#jenkins-setup)
- [GitHub Webhook Configuration](#github-webhook-configuration)
- [Pipeline Triggers](#pipeline-triggers)
- [Log Collection](#log-collection)
- [Testing Failure Scenarios](#testing-failure-scenarios)
- [Docker Deployment](#docker-deployment)

---

## 🎯 Overview

This Next.js todo application includes:

- ✅ Complete CRUD operations for todos
- ✅ RESTful API routes (`/api/todos`, `/api/health`)
- ✅ Jest test suite with coverage reporting
- ✅ Jenkins pipeline with multiple stages (build, test, lint, deploy)
- ✅ Dockerfile for containerization
- ✅ Simulated failure scenarios for testing
- ✅ Comprehensive logging for AIOps analysis

### Tech Stack

- **Framework**: Next.js 14 (React 18, TypeScript)
- **Testing**: Jest, React Testing Library
- **Containerization**: Docker, Docker Compose
- **CI/CD**: Jenkins Pipeline (Jenkinsfile)
- **Build Tool**: npm

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Git
- Jenkins (for CI/CD)
- Docker (optional, for containerization)

### Local Development

1. **Navigate to the demo app directory**:

   ```bash
   cd demo-todo-app
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Run development server**:

   ```bash
   npm run dev
   ```

4. **Open in browser**:

   ```
   http://localhost:3000
   ```

5. **Run tests**:

   ```bash
   npm test              # Watch mode
   npm run test:ci       # CI mode with coverage
   ```

6. **Build for production**:
   ```bash
   npm run build
   npm start
   ```

---

## 🔧 Jenkins Setup

### Step 1: Install Jenkins

#### Windows (Recommended Method)

```powershell
# Download Jenkins WAR file
Invoke-WebRequest -Uri "https://get.jenkins.io/war-stable/latest/jenkins.war" -OutFile "jenkins.war"

# Run Jenkins
java -jar jenkins.war --httpPort=8080
```

#### Alternative: Docker Installation

```bash
docker run -d -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  --name jenkins \
  jenkins/jenkins:lts
```

#### Access Jenkins

1. Open browser: `http://localhost:8080`
2. Get initial admin password:

   ```powershell
   # Windows (if running from WAR)
   Get-Content "$env:USERPROFILE\.jenkins\secrets\initialAdminPassword"

   # Docker
   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```

3. Install suggested plugins
4. Create admin user

### Step 2: Install Required Jenkins Plugins

Navigate to **Manage Jenkins → Manage Plugins → Available**, and install:

- ✅ **Git Plugin** - For repository checkout
- ✅ **Pipeline Plugin** - For Jenkinsfile support
- ✅ **NodeJS Plugin** - For Node.js builds
- ✅ **Docker Pipeline Plugin** - For Docker integration
- ✅ **HTML Publisher Plugin** - For coverage reports
- ✅ **GitHub Plugin** - For GitHub webhooks
- ✅ **JUnit Plugin** - For test result publishing

After installing, restart Jenkins:

```powershell
# If running from WAR, restart the process
# If using Docker:
docker restart jenkins
```

### Step 3: Configure Node.js in Jenkins

1. Go to **Manage Jenkins → Global Tool Configuration**
2. Scroll to **NodeJS** section
3. Click **Add NodeJS**
   - Name: `Node 18`
   - Install automatically: ✅
   - Version: Select Node.js 18.x
4. **Save**

### Step 4: Create Jenkins Pipeline Job

1. **New Item** → Enter name: `aiops-demo-todo-app`
2. Select **Pipeline** → **OK**
3. Configure pipeline:

#### General Settings

- Description: `Demo Todo App for AIOps Log Collection`
- ✅ GitHub project: `https://github.com/YOUR_USERNAME/YOUR_REPO`

#### Build Triggers

Choose one or more:

- ✅ **GitHub hook trigger for GITScm polling** (for webhooks)
- ✅ **Poll SCM**: `H/5 * * * *` (every 5 minutes)
- ✅ **Build periodically**: `H 2 * * *` (daily at 2 AM)

#### Pipeline Configuration

- **Definition**: Pipeline script from SCM
- **SCM**: Git
- **Repository URL**: `https://github.com/YOUR_USERNAME/YOUR_REPO.git`
- **Credentials**: Add your GitHub credentials
- **Branches to build**: `*/main` or `*/master`
- **Script Path**: `demo-todo-app/Jenkinsfile`

4. **Save** and **Build Now** to test

---

## 🔗 GitHub Webhook Configuration

Webhooks automatically trigger Jenkins builds on every push/PR.

### Step 1: Expose Jenkins to Internet

If Jenkins is running locally, you need to expose it:

#### Option A: Using ngrok (Recommended for Testing)

```powershell
# Download ngrok from https://ngrok.com/download
# Extract and run:
ngrok http 8080
```

Copy the **Forwarding URL** (e.g., `https://abc123.ngrok.io`)

#### Option B: Port Forwarding

Configure your router to forward port 8080 to your machine's local IP.

### Step 2: Configure GitHub Webhook

1. **Go to your GitHub repository**
2. **Settings → Webhooks → Add webhook**
3. Configure:
   - **Payload URL**: `https://YOUR_JENKINS_URL/github-webhook/`
     - Example: `https://abc123.ngrok.io/github-webhook/`
   - **Content type**: `application/json`
   - **Secret**: (optional, but recommended)
   - **Which events**: Select:
     - ✅ Just the push event
     - ✅ Pull requests
   - ✅ Active
4. **Add webhook**

### Step 3: Test Webhook

1. Make a change to your repository
2. Commit and push:
   ```bash
   git add .
   git commit -m "Test Jenkins webhook"
   git push origin main
   ```
3. Check Jenkins - build should start automatically!

### Webhook Troubleshooting

**Webhook not triggering?**

- Verify Jenkins URL is accessible from internet
- Check webhook delivery in GitHub (Settings → Webhooks → Recent Deliveries)
- Ensure Jenkins **GitHub Plugin** is installed
- Verify **GitHub hook trigger** is enabled in job configuration

---

## 🎬 Pipeline Triggers

The Jenkins pipeline can be triggered in multiple ways:

### 1. **Manual Trigger**

- Jenkins Dashboard → Select Job → **Build Now**

### 2. **GitHub Webhook** (Automatic)

- Triggers on every `git push` or Pull Request
- See [GitHub Webhook Configuration](#github-webhook-configuration)

### 3. **SCM Polling**

- Jenkins checks repository every 5 minutes for changes
- Configure in Build Triggers: `H/5 * * * *`

### 4. **Scheduled Builds**

- Daily builds at 2 AM: `H 2 * * *`
- Every hour: `H * * * *`
- Configure in Build Triggers → Build periodically

### 5. **REST API Trigger**

```powershell
# Trigger build via API
Invoke-WebRequest -Uri "http://localhost:8080/job/aiops-demo-todo-app/build" `
  -Method POST `
  -Headers @{
    "Authorization" = "Basic $([Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes('username:API_TOKEN')))"
  }
```

---

## 📊 Log Collection

### Accessing Jenkins Build Logs

#### Via Jenkins UI

1. **Dashboard → Job → Build History**
2. Click on build number (e.g., `#15`)
3. **Console Output** - view full logs

#### Via REST API

```powershell
# Get latest build console log
$buildNumber = 15
$jobName = "aiops-demo-todo-app"
Invoke-WebRequest -Uri "http://localhost:8080/job/$jobName/$buildNumber/consoleText" `
  -OutFile "build_${buildNumber}.log"
```

#### Automated Log Collection Script

Create `collect_jenkins_logs.ps1` in the main AIOps project:

```powershell
# Save at: G:\Mtech-Project\AIOPS\scripts\collect_jenkins_logs.ps1

param(
    [string]$JenkinsUrl = "http://localhost:8080",
    [string]$JobName = "aiops-demo-todo-app",
    [string]$Username = "admin",
    [string]$ApiToken = "YOUR_API_TOKEN",
    [int]$MaxBuilds = 30
)

$outputDir = "G:\Mtech-Project\AIOPS\data\jenkins_logs"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${ApiToken}"))
$headers = @{ Authorization = "Basic $auth" }

# Get job info
$jobUrl = "$JenkinsUrl/job/$JobName/api/json?tree=builds[number,result,timestamp,duration]"
$jobInfo = Invoke-RestMethod -Uri $jobUrl -Headers $headers

# Download logs for recent builds
$jobInfo.builds | Select-Object -First $MaxBuilds | ForEach-Object {
    $buildNum = $_.number
    $result = $_.result
    $timestamp = $_.timestamp

    Write-Host "Downloading build #$buildNum (${result})..."

    $logUrl = "$JenkinsUrl/job/$JobName/$buildNum/consoleText"
    $logFile = Join-Path $outputDir "build_${buildNum}_${result}.log"

    Invoke-WebRequest -Uri $logUrl -Headers $headers -OutFile $logFile

    # Add metadata
    @{
        build_number = $buildNum
        result = $result
        timestamp = $timestamp
        duration = $_.duration
    } | ConvertTo-Json | Out-File -FilePath "$logFile.meta.json"
}

Write-Host "Collected logs saved to: $outputDir"
```

**Usage**:

```powershell
# Get API token from Jenkins: User → Configure → API Token
.\scripts\collect_jenkins_logs.ps1 -ApiToken "YOUR_TOKEN_HERE"
```

### Log Format

Jenkins console logs include:

- **Build metadata** (number, timestamp, Git commit)
- **Environment information** (Node version, npm version)
- **Dependency installation** logs
- **Linting** output (ESLint warnings/errors)
- **Test results** (Jest output, coverage)
- **Build process** logs (Next.js build)
- **Docker build** logs (if on main branch)
- **Security scan** results (npm audit)
- **Performance metrics** (build size)
- **Final status** (SUCCESS, FAILURE, UNSTABLE)

---

## 💥 Testing Failure Scenarios

The pipeline includes intentional failure scenarios for testing AIOps failure prediction.

### Enable Failure Simulation

Edit `Jenkinsfile` and set:

```groovy
environment {
    SIMULATE_FAILURE = 'true'  // Change from 'false' to 'true'
}
```

### Failure Patterns

When `SIMULATE_FAILURE = 'true'`:

| Build #   | Failure Type         | Stage                |
| --------- | -------------------- | -------------------- |
| Every 3rd | **Test Failure**     | Run Tests            |
| Every 5th | **Dependency Error** | Install Dependencies |
| Every 7th | **Build Failure**    | Build Application    |

**Example**:

- Build #3: Tests fail
- Build #5: Dependencies fail
- Build #6: Normal (SUCCESS)
- Build #7: Build fails
- Build #9: Tests fail
- Build #10: Dependencies fail

### Manual Failure Injection

#### 1. Breaking Tests

Edit `__tests__/Home.test.tsx`:

```typescript
it("should fail intentionally", () => {
  expect(1 + 1).toBe(3); // Intentional failure
});
```

#### 2. Build Errors

Edit `app/page.tsx`:

```typescript
const invalidSyntax =   // Syntax error for testing
```

#### 3. Dependency Issues

Edit `package.json`:

```json
"dependencies": {
  "nonexistent-package": "1.0.0"  // Invalid package
}
```

### Analyzing Failure Logs

Failed builds generate rich error logs:

- **Stack traces**
- **Error messages**
- **Failed test output**
- **Build errors with line numbers**
- **Exit codes**

These logs are essential for training the AIOps failure prediction model.

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
cd demo-todo-app
docker build -t aiops-demo-todo-app:latest .
```

### Run with Docker Compose

```bash
docker-compose up -d
```

### Access Application

```
http://localhost:3000
```

### Stop Application

```bash
docker-compose down
```

### View Logs

```bash
docker-compose logs -f todo-app
```

---

## 📁 Project Structure

```
demo-todo-app/
├── app/                      # Next.js App Router
│   ├── api/                  # API routes
│   │   ├── todos/            # Todo CRUD endpoints
│   │   │   ├── route.ts      # GET, POST, DELETE /api/todos
│   │   │   └── [id]/route.ts # GET, PUT, DELETE /api/todos/:id
│   │   └── health/           # Health check endpoint
│   │       └── route.ts      # GET /api/health
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Home page (Todo UI)
│   ├── page.module.css       # Page styles
│   └── globals.css           # Global styles
├── __tests__/                # Jest test suite
│   ├── Home.test.tsx         # Home page tests
│   ├── api-todos.test.ts     # Todo API tests
│   └── api-health.test.ts    # Health check tests
├── Jenkinsfile               # Jenkins pipeline configuration
├── Dockerfile                # Multi-stage Docker build
├── docker-compose.yml        # Docker Compose configuration
├── package.json              # Dependencies and scripts
├── tsconfig.json             # TypeScript configuration
├── jest.config.js            # Jest configuration
├── jest.setup.js             # Jest setup file
├── next.config.js            # Next.js configuration
├── .eslintrc.js              # ESLint configuration
├── .gitignore                # Git ignore patterns
├── .dockerignore             # Docker ignore patterns
└── README.md                 # This file
```

---

## 🔌 Integration with AIOps System

### Jenkins Collector Configuration

The main AIOps system includes a Jenkins collector at:

```
G:\Mtech-Project\AIOPS\collectors\jenkins_collector.py
```

**Update `.env` in main project**:

```bash
# Jenkins Configuration
JENKINS_URL=http://localhost:8080
JENKINS_USER=admin
JENKINS_TOKEN=YOUR_API_TOKEN_HERE
JENKINS_JOB=aiops-demo-todo-app
```

**Collect logs**:

```powershell
cd G:\Mtech-Project\AIOPS
python collectors/jenkins_collector.py
```

This will:

1. Connect to Jenkins
2. Retrieve build metadata and console logs
3. Extract features (errors, warnings, duration)
4. Save to `data/jenkins_logs/` for training

---

## 🎯 Next Steps

1. **✅ Set up Jenkins** following [Jenkins Setup](#jenkins-setup)
2. **✅ Configure GitHub webhooks** for automatic builds
3. **✅ Run multiple builds** to generate log data (at least 20-30 builds)
4. **✅ Enable failure simulation** to create diverse training data
5. **✅ Collect logs** using `jenkins_collector.py`
6. **✅ Train AIOps models** using collected data

---

## 📞 Troubleshooting

### Build Fails with "Node not found"

- Install NodeJS plugin in Jenkins
- Configure Node 18 in Global Tool Configuration
- Ensure `node` is in PATH

### Tests Fail Locally

```bash
npm install
npm run test
```

### Docker Build Fails

- Ensure Next.js config has `output: 'standalone'` (if using)
- Check Docker daemon is running
- Try: `docker system prune -a` to clean cache

### Webhook Not Triggering

- Verify ngrok/public URL is accessible
- Check webhook delivery in GitHub
- Ensure GitHub Plugin is installed
- Test with manual "Poll SCM" first

---

## 📝 License

This is a demo project for educational purposes as part of the AIOps system.

---

**Happy Testing! 🚀**

For questions about the main AIOps system, see: `G:\Mtech-Project\AIOPS\README.md`

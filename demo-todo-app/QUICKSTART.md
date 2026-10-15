# Quick Start Guide - Demo Todo App

Get up and running with the Jenkins pipeline in 15 minutes!

## Prerequisites Checklist

- ✅ Windows 10/11
- ✅ Node.js 18+ installed ([Download](https://nodejs.org))
- ✅ Git installed ([Download](https://git-scm.com/download/win))
- ✅ Java 11+ installed (for Jenkins) ([Download](https://adoptium.net))

---

## Step 1: Setup Project (2 minutes)

```powershell
# Navigate to demo app
cd G:\Mtech-Project\AIOPS\demo-todo-app

# Install dependencies
npm install

# Verify installation
npm run build
```

**Expected output**: `✓ Compiled successfully`

---

## Step 2: Install Jenkins (3 minutes)

### Download Jenkins

```powershell
# Download latest stable version
Invoke-WebRequest -Uri "https://get.jenkins.io/war-stable/latest/jenkins.war" -OutFile "jenkins.war"

# Or download manually from: https://www.jenkins.io/download/
```

### Start Jenkins

```powershell
# Run Jenkins (keep this terminal open)
java -jar jenkins.war --httpPort=8080
```

### Initial Setup

1. Open browser: `http://localhost:8080`
2. Copy password from terminal or:
   ```powershell
   Get-Content "$env:USERPROFILE\.jenkins\secrets\initialAdminPassword"
   ```
3. Click **Install suggested plugins** (wait 2-3 minutes)
4. Create admin user:
   - Username: `admin`
   - Password: `your_password`
   - Full name: `Your Name`
   - Email: `your@email.com`
5. Click **Save and Continue → Save and Finish → Start using Jenkins**

---

## Step 3: Configure Jenkins (5 minutes)

### Install Required Plugins

1. **Manage Jenkins → Manage Plugins → Available**
2. Search and install:
   - ✅ NodeJS Plugin
   - ✅ Git Plugin
   - ✅ GitHub Plugin
   - ✅ HTML Publisher Plugin
3. **Restart Jenkins** (check "Restart when no jobs are running")

### Configure Node.js

1. **Manage Jenkins → Global Tool Configuration**
2. Scroll to **NodeJS**
3. Click **Add NodeJS**
   - Name: `Node 18`
   - ✅ Install automatically
   - Version: Select `NodeJS 18.x.x`
4. **Save**

---

## Step 4: Create Jenkins Job (3 minutes)

### Create Pipeline Job

1. **New Item**
2. Item name: `aiops-demo-todo-app`
3. Select **Pipeline** → **OK**

### Configure Job

**Build Triggers**:

- ✅ Poll SCM: `H/5 * * * *` (checks every 5 minutes)

**Pipeline**:

- Definition: **Pipeline script from SCM**
- SCM: **Git**
- Repository URL: `file:///G:/Mtech-Project/AIOPS` (for local testing)
  - OR your GitHub URL: `https://github.com/YOUR_USERNAME/YOUR_REPO.git`
- Branch: `*/main`
- Script Path: `demo-todo-app/Jenkinsfile`

**Save** → **Build Now**

---

## Step 5: Monitor First Build (2 minutes)

1. Watch **Build History** (bottom left)
2. Click on `#1` when it appears
3. Click **Console Output**
4. Watch the build progress!

**Expected stages**:

```
✓ Environment Info
✓ Checkout
✓ Install Dependencies
✓ Lint
✓ Run Tests
✓ Build Application
✓ Security Scan
✓ Performance Check
```

**First build** will take 2-3 minutes (downloading dependencies).

---

## Step 6: Trigger More Builds

### Option A: Make Code Changes

```bash
# Make a small change
echo "" >> README.md

# Commit
git add .
git commit -m "Test Jenkins build"

# If using local repository, Jenkins will detect changes in 5 minutes
# Or click "Build Now" in Jenkins
```

### Option B: Manual Trigger

- Jenkins Dashboard → Job → **Build Now**

### Option C: Scheduled Builds

Already configured to check for changes every 5 minutes!

---

## Step 7: Enable Failure Simulation (Optional)

To test failure scenarios:

1. Edit `demo-todo-app/Jenkinsfile`
2. Change line 8:
   ```groovy
   SIMULATE_FAILURE = 'true'  // was 'false'
   ```
3. Commit and push
4. Watch builds fail in interesting ways!

---

## Step 8: Collect Logs for AIOps

### Get Jenkins API Token

1. Click your username (top right)
2. **Configure**
3. **API Token → Add new Token**
4. Name: `Log Collection`
5. **Generate** → Copy token

### Run Collection Script

```powershell
cd G:\Mtech-Project\AIOPS
.\scripts\collect_jenkins_logs.ps1 -ApiToken "YOUR_TOKEN_HERE"
```

**Output**:

```
✓ Output directory: G:\Mtech-Project\AIOPS\data\jenkins_logs
✓ Successfully connected to Jenkins
✓ Found 10 builds
...
Summary: 10 logs downloaded
```

---

## Troubleshooting

### Build fails with "node: command not found"

- Verify NodeJS plugin installed
- Check Global Tool Configuration has Node 18
- Restart Jenkins

### Build fails with "Checkout" error

- Verify Git is installed: `git --version`
- Check repository URL is correct
- Ensure branch name matches (main vs master)

### Tests fail

```powershell
# Run tests locally first
cd demo-todo-app
npm test
```

### Can't access Jenkins

- Check Java is running: `java -version`
- Verify port 8080 is not in use
- Check firewall settings

---

## Next Steps

✅ **You're ready!** You now have:

- Working Jenkins pipeline
- Automated builds every 5 minutes
- Test results and coverage reports
- Build logs ready for collection

### To Set Up GitHub Webhooks:

See detailed guide: `WEBHOOK_SETUP.md`

### To Test Failure Scenarios:

See detailed guide: `FAILURE_SCENARIOS.md`

### To Collect Logs at Scale:

```powershell
# Run this daily/weekly
.\scripts\collect_jenkins_logs.ps1 -ApiToken "YOUR_TOKEN" -MaxBuilds 50
```

---

## Quick Reference

### Start Jenkins

```powershell
java -jar jenkins.war --httpPort=8080
```

### Access Jenkins

```
http://localhost:8080
Username: admin
Password: your_password
```

### Run Local Build

```powershell
cd demo-todo-app
npm install
npm test
npm run build
```

### Collect Logs

```powershell
.\scripts\collect_jenkins_logs.ps1 -ApiToken "YOUR_TOKEN"
```

---

**Need more help?** See full documentation: `README.md`

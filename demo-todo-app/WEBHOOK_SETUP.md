# GitHub Webhook Setup Guide

Complete guide for configuring GitHub webhooks to automatically trigger Jenkins builds.

## Prerequisites

- ✅ Jenkins installed and running
- ✅ GitHub repository created
- ✅ Jenkins accessible from the internet (via ngrok, port forwarding, or public server)

---

## Step 1: Make Jenkins Accessible from Internet

Jenkins must be accessible from the internet for GitHub to send webhook events.

### Option A: Using ngrok (Easiest for Local Testing)

1. **Download ngrok**:

   - Visit: https://ngrok.com/download
   - Download for Windows
   - Extract `ngrok.exe`

2. **Sign up and get auth token**:

   - Create free account at https://dashboard.ngrok.com
   - Copy your authtoken

3. **Authenticate ngrok**:

   ```powershell
   .\ngrok.exe authtoken YOUR_AUTH_TOKEN
   ```

4. **Start ngrok tunnel**:

   ```powershell
   .\ngrok.exe http 8080
   ```

5. **Copy the Forwarding URL**:
   ```
   Forwarding  https://abc123.ngrok.io -> http://localhost:8080
   ```
   ☝️ This is your public Jenkins URL: `https://abc123.ngrok.io`

**Important**: Keep ngrok running! Closing it will break the webhook.

### Option B: Router Port Forwarding (For Permanent Setup)

1. **Find your local IP**:

   ```powershell
   ipconfig
   # Look for IPv4 Address (e.g., 192.168.1.100)
   ```

2. **Configure router**:

   - Access router admin panel (usually `192.168.1.1`)
   - Navigate to Port Forwarding settings
   - Add rule:
     - External Port: `8080`
     - Internal IP: Your computer's IP (e.g., `192.168.1.100`)
     - Internal Port: `8080`
     - Protocol: `TCP`
   - Save and apply

3. **Find your public IP**:

   ```powershell
   Invoke-RestMethod -Uri "https://api.ipify.org?format=json" | Select-Object -ExpandProperty ip
   ```

4. **Your Jenkins URL**:
   ```
   http://YOUR_PUBLIC_IP:8080
   ```

**Security Note**: Expose Jenkins only if you understand the security implications. Use strong passwords and consider HTTPS.

### Option C: Deploy Jenkins on Cloud Server (Production)

Deploy Jenkins on Azure, AWS, or GCP for a permanent public URL.

---

## Step 2: Configure Jenkins for GitHub Webhooks

### 2.1 Install GitHub Plugin

1. **Manage Jenkins → Manage Plugins**
2. **Available** tab
3. Search: `GitHub Plugin`
4. ✅ Select and **Install without restart**
5. Wait for installation to complete

### 2.2 Configure GitHub Server (Optional)

1. **Manage Jenkins → Configure System**
2. Scroll to **GitHub** section
3. Click **Add GitHub Server**
   - Name: `GitHub`
   - API URL: `https://api.github.com` (default)
   - Credentials: Add GitHub personal access token (optional, for private repos)
4. **Save**

### 2.3 Create GitHub Personal Access Token (For Private Repos)

1. Go to GitHub: **Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. **Generate new token (classic)**
3. Configure:
   - Note: `Jenkins Webhook Access`
   - Expiration: `90 days` or `No expiration`
   - Scopes:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `admin:repo_hook` (Full control of repository hooks)
4. **Generate token**
5. **Copy token** (you won't see it again!)

6. **Add to Jenkins**:
   - Manage Jenkins → Manage Credentials
   - Click on domain (e.g., `(global)`)
   - **Add Credentials**
   - Kind: `Secret text`
   - Secret: Paste your token
   - ID: `github-token`
   - Description: `GitHub PAT for webhooks`
   - **Create**

---

## Step 3: Configure Jenkins Job for Webhooks

1. **Open your Jenkins job** (`aiops-demo-todo-app`)
2. **Configure**
3. **Build Triggers** section:
   - ✅ **GitHub hook trigger for GITScm polling**
4. **Source Code Management** section:
   - Select **Git**
   - Repository URL: `https://github.com/YOUR_USERNAME/YOUR_REPO.git`
   - Credentials: Select your GitHub credentials (if private repo)
   - Branch: `*/main` or `*/master`
5. **Save**

---

## Step 4: Configure GitHub Webhook

### 4.1 Navigate to Repository Settings

1. Go to your GitHub repository
2. **Settings** (top right)
3. **Webhooks** (left sidebar)
4. **Add webhook**

### 4.2 Configure Webhook

**Payload URL**:

```
https://YOUR_JENKINS_URL/github-webhook/
```

Examples:

- ngrok: `https://abc123.ngrok.io/github-webhook/`
- Public IP: `http://123.45.67.89:8080/github-webhook/`
- Cloud: `https://jenkins.yourdomain.com/github-webhook/`

⚠️ **Important**: Don't forget the trailing `/`!

**Content type**:

- Select: `application/json`

**Secret** (Optional but recommended):

- Generate a secret key:
  ```powershell
  # Generate random secret
  -join ((65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
  ```
- Paste in Secret field
- Save this secret for Jenkins configuration (if needed)

**Which events would you like to trigger this webhook?**

- Select: `Just the push event` (recommended for simplicity)
- Or: `Let me select individual events`
  - ✅ Pushes
  - ✅ Pull requests

**Active**:

- ✅ Ensure this checkbox is selected

**Add webhook**

---

## Step 5: Test the Webhook

### 5.1 Make a Test Commit

```bash
# Make a small change
echo "# Test webhook" >> README.md

# Commit and push
git add README.md
git commit -m "Test Jenkins webhook trigger"
git push origin main
```

### 5.2 Verify in GitHub

1. Go to repository **Settings → Webhooks**
2. Click on your webhook
3. Scroll to **Recent Deliveries**
4. You should see a delivery with:
   - ✅ Green checkmark (200 response)
   - Request and Response details

### 5.3 Verify in Jenkins

1. Go to Jenkins Dashboard
2. Your job should start building automatically
3. Check **Build History** for the new build

---

## Step 6: Troubleshooting

### Webhook shows red X (failed delivery)

**Check 1: Jenkins URL is accessible**

```powershell
# Test from another machine or use an online tool like:
# https://reqbin.com/

curl https://YOUR_JENKINS_URL/github-webhook/
```

**Check 2: Firewall blocking requests**

- Ensure Windows Firewall allows inbound on port 8080
- Check antivirus/security software

**Check 3: ngrok connection dropped**

- Restart ngrok
- Update webhook URL with new ngrok URL

### Webhook delivers but Jenkins doesn't build

**Check 1: GitHub hook trigger enabled**

- Job → Configure → Build Triggers
- Ensure ✅ **GitHub hook trigger for GITScm polling**

**Check 2: GitHub Plugin installed**

- Manage Jenkins → Manage Plugins
- Verify GitHub Plugin is installed and enabled

**Check 3: Repository URL matches**

- Webhook is on correct repository
- Jenkins job is configured for same repository

### Webhook delivers to wrong endpoint

**Correct URL format**:

```
https://YOUR_JENKINS_URL/github-webhook/
```

**NOT**:

- ❌ `https://YOUR_JENKINS_URL/job/aiops-demo-todo-app/build`
- ❌ `https://YOUR_JENKINS_URL/github-webhook` (missing trailing slash)
- ❌ `https://YOUR_JENKINS_URL/webhooks/github`

### "Couldn't find any revision to build"

**Solution**: Make sure your branch name in Jenkins job configuration matches your actual branch:

- Check repository default branch (main or master)
- Update Jenkins job: Configure → Branches to build → `*/main`

---

## Step 7: Advanced Configuration

### Multiple Branch Builds

Configure job to build multiple branches:

- Branches to build: `*/*` (all branches)
- Or specific patterns: `*/feature-*`, `*/bugfix-*`

### Pull Request Builds

1. Install **GitHub Pull Request Builder** plugin
2. Configure job:
   - Build Triggers: ✅ GitHub Pull Request Builder
   - Add PR builds to your workflow

### Webhook Security

1. **Generate webhook secret** (Step 4.2)
2. **Configure Jenkins**:
   - Manage Jenkins → Configure System
   - GitHub section → Advanced
   - Add webhook secret validation

### Notification on Build Status

Update your Jenkinsfile `post` section:

```groovy
post {
    success {
        // Notify success (can integrate with Slack, email, etc.)
    }
    failure {
        // Notify failure
    }
}
```

---

## Step 8: Webhook Events Reference

Common GitHub events you can trigger on:

| Event          | Description                     | Use Case              |
| -------------- | ------------------------------- | --------------------- |
| `push`         | Code pushed to repository       | Standard CI builds    |
| `pull_request` | PR opened, synchronized, closed | PR validation         |
| `create`       | Branch or tag created           | Deploy new features   |
| `delete`       | Branch or tag deleted           | Cleanup               |
| `release`      | Release published               | Production deployment |

---

## Summary Checklist

- ✅ Jenkins accessible from internet (ngrok/port forward/cloud)
- ✅ GitHub Plugin installed in Jenkins
- ✅ Jenkins job configured with "GitHub hook trigger"
- ✅ GitHub webhook created with correct URL format
- ✅ Webhook shows green checkmark in Recent Deliveries
- ✅ Test commit triggers automatic build
- ✅ Build logs show trigger source as GitHub webhook

---

## Quick Reference Commands

### Test Jenkins Webhook Endpoint

```powershell
Invoke-WebRequest -Uri "https://YOUR_JENKINS_URL/github-webhook/" -Method POST
```

### Check ngrok Status

```powershell
# View active tunnels
Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
```

### View Recent Webhook Deliveries via API

```powershell
$repo = "YOUR_USERNAME/YOUR_REPO"
$token = "YOUR_GITHUB_TOKEN"
$headers = @{ Authorization = "token $token" }

Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/hooks" -Headers $headers
```

---

**Need Help?** See main README: `demo-todo-app/README.md`

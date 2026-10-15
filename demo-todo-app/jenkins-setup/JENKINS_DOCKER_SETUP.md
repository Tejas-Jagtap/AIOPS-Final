# Jenkins Docker Setup Guide for Windows

This guide helps you set up Jenkins with Docker support on Windows (Docker Desktop).

## Prerequisites

- Docker Desktop for Windows installed and running
- WSL 2 backend enabled (recommended)

## Option 1: Simple Setup (Current Approach - No Docker in Pipeline)

Your current `Jenkinsfile` downloads Node.js directly, so you **don't need** Docker-in-Docker. This is the simplest approach.

Just push your code and run the build - it will work!

---

## Option 2: Jenkins with Docker Socket (For Docker Pipeline Plugin)

If you want Jenkins to run Docker commands (for `Jenkinsfile.docker`), follow these steps:

### Step 1: Check your current Jenkins container name

```powershell
docker ps -a | Select-String jenkins
```

### Step 2: Stop and remove the existing Jenkins container

```powershell
docker stop jenkins
docker rm jenkins
```

> ⚠️ **Note**: Your Jenkins data is stored in a volume (`jenkins_home`), so you won't lose any configuration.

### Step 3: Create a new Jenkins container with Docker socket access

**For Windows with Docker Desktop (WSL 2 backend):**

```powershell
docker run -d `
  --name jenkins `
  --restart unless-stopped `
  --privileged `
  -p 8080:8080 `
  -p 50000:50000 `
  -v jenkins_home:/var/jenkins_home `
  -v /var/run/docker.sock:/var/run/docker.sock `
  jenkins/jenkins:lts-jdk17
```

### Step 4: Install Docker CLI inside Jenkins container

```powershell
# Enter the Jenkins container as root
docker exec -u root -it jenkins bash

# Inside the container, install Docker CLI
apt-get update
apt-get install -y docker.io

# Fix permissions for docker socket
chmod 666 /var/run/docker.sock

# Verify Docker works
docker --version
docker ps

# Exit the container
exit
```

### Step 5: Install Docker Pipeline Plugin in Jenkins

1. Go to http://localhost:8080
2. Navigate to: **Manage Jenkins** → **Plugins** → **Available plugins**
3. Search for: `Docker Pipeline`
4. Install it and restart Jenkins

### Step 6: Test Docker access

Create a test pipeline with this script:

```groovy
pipeline {
    agent {
        docker {
            image 'node:22-slim'
        }
    }
    stages {
        stage('Test') {
            steps {
                sh 'node --version'
            }
        }
    }
}
```

---

## Option 3: Docker-in-Docker (DinD) - More Isolated

This runs a separate Docker daemon inside Jenkins (more isolated but more complex).

### Using Docker Compose

Save this as `docker-compose.yml`:

```yaml
version: "3.8"

services:
  jenkins:
    image: jenkins/jenkins:lts-jdk17
    container_name: jenkins
    privileged: true
    user: root
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock

volumes:
  jenkins_home:
```

Run with:

```powershell
docker-compose up -d
```

---

## Troubleshooting

### "Permission denied" on Docker socket

```powershell
docker exec -u root jenkins chmod 666 /var/run/docker.sock
```

### "docker: command not found" in Jenkins

```powershell
docker exec -u root -it jenkins bash -c "apt-get update && apt-get install -y docker.io"
```

### Check if Docker socket is mounted

```powershell
docker exec jenkins ls -la /var/run/docker.sock
```

### Verify Docker works from Jenkins

```powershell
docker exec jenkins docker ps
```

---

## Recommended Approach

For your **AIOps Demo Todo App**, the simplest approach is:

1. **Use the current `Jenkinsfile`** (downloads Node.js directly)
2. **No Docker setup required**
3. Just push and build!

The Docker agent approach (`Jenkinsfile.docker`) is only needed if you want:

- Cleaner builds (isolated containers)
- Different Node.js versions per branch
- Building Docker images in the pipeline

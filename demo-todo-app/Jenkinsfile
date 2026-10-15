// Alternative Jenkinsfile for environments without Docker access
// This version manually downloads and sets up Node.js
pipeline {
    agent any
    
    environment {
        NODE_VERSION = '22.15.0'
        APP_NAME = 'aiops-demo-todo-app'
        SIMULATE_FAILURE = 'false'
        NPM_CONFIG_UPDATE_NOTIFIER = 'false'
        CI = 'true'
        // Node.js will be installed in workspace
        NODEJS_HOME = "${WORKSPACE}/.nodejs"
        PATH = "${WORKSPACE}/.nodejs/bin:${env.PATH}"
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '30', daysToKeepStr: '30'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }
    
    stages {
        stage('Setup Node.js') {
            steps {
                echo 'Downloading and setting up Node.js...'
                sh '''
                    # Create directory for Node.js
                    mkdir -p ${WORKSPACE}/.nodejs
                    
                    # Download Node.js if not already present
                    if [ ! -f "${WORKSPACE}/.nodejs/bin/node" ]; then
                        echo "Downloading Node.js ${NODE_VERSION}..."
                        # Use .tar.gz instead of .tar.xz (xz not available in Jenkins container)
                        curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.gz" -o node.tar.gz
                        
                        echo "Extracting Node.js..."
                        tar -xzf node.tar.gz --strip-components=1 -C ${WORKSPACE}/.nodejs
                        rm node.tar.gz
                        
                        echo "Node.js installed successfully"
                    else
                        echo "Node.js already present"
                    fi
                    
                    # Verify installation
                    export PATH="${WORKSPACE}/.nodejs/bin:${PATH}"
                    node --version
                    npm --version
                '''
            }
        }
        
        stage('Environment Info') {
            steps {
                echo '========================================='
                echo 'AIOps Demo Todo App - Jenkins Pipeline'
                echo '========================================='
                echo "Build Number: ${env.BUILD_NUMBER}"
                echo "Build ID: ${env.BUILD_ID}"
                echo "Node Version: ${NODE_VERSION}"
                echo "Jenkins URL: ${env.JENKINS_URL}"
                echo "Workspace: ${env.WORKSPACE}"
                echo '========================================='
                
                sh '''
                    export PATH="${WORKSPACE}/.nodejs/bin:${PATH}"
                    node --version
                    npm --version
                    git --version
                '''
            }
        }
        
        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
                sh 'git log -1 --pretty=format:"%h - %an, %ar : %s"'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo 'Installing Node.js dependencies...'
                sh '''
                    export PATH="${WORKSPACE}/.nodejs/bin:${PATH}"
                    npm install --legacy-peer-deps
                '''
                echo 'Dependencies installed successfully'
            }
        }
        
        stage('Lint') {
            steps {
                echo 'Running ESLint...'
                script {
                    try {
                        sh '''
                            export PATH="${WORKSPACE}/.nodejs/bin:${PATH}"
                            npm run lint
                        '''
                        echo 'Linting passed successfully'
                    } catch (Exception e) {
                        echo "WARNING: Linting issues detected: ${e.message}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                echo 'Running Jest test suite...'
                sh '''
                    export PATH="${WORKSPACE}/.nodejs/bin:${PATH}"
                    npm run test:ci
                '''
                echo 'All tests passed successfully'
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'coverage/junit.xml'
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'coverage',
                        reportFiles: 'index.html',
                        reportName: 'Test Coverage Report'
                    ])
                }
            }
        }
        
        stage('Build Application') {
            steps {
                echo 'Building Next.js application...'
                sh '''
                    export PATH="${WORKSPACE}/.nodejs/bin:${PATH}"
                    npm run build
                '''
                echo 'Application built successfully'
                sh 'ls -lah .next'
            }
        }
        
        stage('Security Scan') {
            steps {
                echo 'Running npm audit...'
                script {
                    try {
                        sh '''
                            export PATH="${WORKSPACE}/.nodejs/bin:${PATH}"
                            npm audit --audit-level=moderate
                        '''
                        echo 'No critical vulnerabilities found'
                    } catch (Exception e) {
                        echo "WARNING: Security vulnerabilities detected"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Performance Check') {
            steps {
                echo 'Analyzing build size...'
                sh '''
                    echo "Build Statistics:"
                    du -sh .next
                    echo "Static Files:"
                    du -sh .next/static 2>/dev/null || echo "No static files"
                '''
            }
        }
    }
    
    post {
        always {
            echo '========================================='
            echo 'Pipeline Execution Complete'
            echo '========================================='
            echo "Build Result: ${currentBuild.result ?: 'SUCCESS'}"
            echo "Duration: ${currentBuild.durationString}"
            echo "Build Number: ${env.BUILD_NUMBER}"
            echo '========================================='
        }
        
        success {
            echo '✓ Build completed successfully!'
        }
        
        failure {
            echo '✗ Build failed!'
        }
        
        unstable {
            echo '⚠ Build is unstable'
        }
    }
}

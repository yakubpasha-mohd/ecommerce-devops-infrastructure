pipeline {

    agent any

    options {
        timestamps()
        ansiColor('xterm')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        choice(
            name: 'SERVICE',
            choices: ['user-service'],
            description: 'Microservice to build in Phase 3.5'
        )

        string(
            name: 'APP_REPO_URL',
            defaultValue: 'https://github.com/yakubpasha-mohd/ecommerce.git',
            description: 'E-commerce application Git repository'
        )

        string(
            name: 'APP_BRANCH',
            defaultValue: 'main',
            description: 'Application Git branch'
        )

        booleanParam(
            name: 'RUN_DEPENDENCY_CHECK',
            defaultValue: false,
            description: 'Run OWASP Dependency-Check'
        )

        booleanParam(
            name: 'PUSH_ECR',
            defaultValue: false,
            description: 'Push Docker images to AWS ECR'
        )

        string(
            name: 'AWS_REGION',
            defaultValue: 'us-east-1',
            description: 'AWS region for ECR'
        )

        string(
            name: 'ECR_BACKEND_REPOSITORY',
            defaultValue: 'ecommerce/user-service',
            description: 'ECR repository for user-service'
        )

        string(
            name: 'ECR_FRONTEND_REPOSITORY',
            defaultValue: 'ecommerce/frontend',
            description: 'ECR repository for frontend'
        )
    }

    environment {
        APP_DIR = 'ecommerce-app'
        SERVICE_DIR = 'ecommerce-app/services/user-service'
        FRONTEND_DIR = 'ecommerce-app/services/frontend'

        BACKEND_IMAGE = "ecommerce-user-service:${BUILD_NUMBER}"
        FRONTEND_IMAGE = "ecommerce-frontend:${BUILD_NUMBER}"

        TRIVY_CACHE_DIR = "${WORKSPACE}/.trivy-cache"
    }

    stages {

        stage('Checkout') {
            steps {
                echo '============================================================'
                echo 'CHECKOUT DEVOPS REPOSITORY'
                echo '============================================================'

                checkout scm

                echo '============================================================'
                echo 'CHECKOUT E-COMMERCE APPLICATION'
                echo '============================================================'

                dir(env.APP_DIR) {
                    git(
                        url: params.APP_REPO_URL,
                        branch: params.APP_BRANCH,
                        credentialsId: 'github-ecommerce-devops',
                        changelog: false,
                        poll: false
                    )
                }

                echo 'CHECKOUT COMPLETED'
            }
        }

        stage('Workspace Info') {
            steps {
                sh '''
                    set -eux

                    echo "SYSTEM INFORMATION"
                    java -version
                    mvn -version
                    node --version
                    npm --version
                    docker --version
                    aws --version
                    trivy --version
                    semgrep --version
                    checkov --version

                    echo "WORKSPACE"
                    pwd
                    ls -la

                    echo "APPLICATION DIRECTORY"
                    ls -la "$APP_DIR"

                    echo "APPLICATION GIT COMMIT"
                    git -C "$APP_DIR" rev-parse HEAD
                '''
            }
        }

        stage('Maven Build & Unit Test') {
            steps {
                dir(env.SERVICE_DIR) {
                    sh '''
                        set -eux

                        echo "MAVEN BUILD & UNIT TEST"

                        mvn -B -ntp clean verify

                        echo "MAVEN BUILD SUCCESSFUL"

                        find target                           -maxdepth 2                           -type f                           -name '*.jar'                           -print
                    '''
                }
            }

            post {
                always {
                    junit(
                        allowEmptyResults: true,
                        testResults: 'ecommerce-app/services/user-service/target/surefire-reports/*.xml'
                    )
                }
            }
        }

        stage('Frontend Build') {
            steps {
                dir(env.FRONTEND_DIR) {
                    sh '''
                        set -eux

                        echo "FRONTEND BUILD"

                        test -f package.json

                        npm install --no-audit --no-fund

                        npm run build

                        test -d dist

                        echo "FRONTEND BUILD COMPLETED"
                        ls -lah dist
                    '''
                }
            }
        }

        stage('Static Security - Semgrep') {
            steps {
                sh '''
                    set -eux

                    semgrep scan                       --config p/java                       --config p/typescript                       --error                       --exclude node_modules                       --exclude target                       --exclude dist                       --exclude .trivy-cache                       .
                '''
            }
        }

        stage('Filesystem Security - Trivy') {
            steps {
                sh '''
                    set -eux

                    mkdir -p "$TRIVY_CACHE_DIR"

                    trivy fs                       --scanners vuln,secret,misconfig                       --exit-code 1                       --severity CRITICAL,HIGH                       --ignore-unfixed                       --cache-dir "$TRIVY_CACHE_DIR"                       .
                '''
            }
        }

        stage('Dependency Security - OWASP') {
            when {
                expression {
                    params.RUN_DEPENDENCY_CHECK
                }
            }

            steps {
                dir(env.SERVICE_DIR) {
                    sh '''
                        set -eux

                        mvn -B -ntp                           -DskipTests                           org.owasp:dependency-check-maven:check                           -DfailBuildOnCVSS=7
                    '''
                }
            }
        }

        stage('SonarQube') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'sonar-token',
                        variable: 'SONAR_TOKEN'
                    )
                ]) {
                    withSonarQubeEnv('SonarQube') {
                        sh '''
                            set -eux

                            test -f "$SERVICE_DIR/pom.xml"

                            mvn -B -ntp                               -f "$SERVICE_DIR/pom.xml"                               -DskipTests                               -Dsonar.projectKey=ecommerce-user-service                               -Dsonar.projectName=ecommerce-user-service                               -Dsonar.host.url="$SONAR_HOST_URL"                               -Dsonar.token="$SONAR_TOKEN"                               org.sonarsource.scanner.maven:sonar-maven-plugin:sonar
                        '''
                    }

                    timeout(time: 10, unit: 'MINUTES') {
                        script {
                            def qualityGate = waitForQualityGate(
                                abortPipeline: false
                            )

                            echo "SONARQUBE QUALITY GATE STATUS: ${qualityGate.status}"

                            if (qualityGate.status != 'OK') {
                                error(
                                    "SonarQube Quality Gate failed: ${qualityGate.status}"
                                )
                            }
                        }
                    }
                }
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    env.GIT_SHA = sh(
                        script: 'git -C "$APP_DIR" rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    env.GIT_SHORT_SHA = sh(
                        script: 'git -C "$APP_DIR" rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }

                sh '''
                    set -eux

                    echo "DOCKER BUILD - USER SERVICE"

                    test -f "$SERVICE_DIR/Dockerfile"
                    test -f "$SERVICE_DIR/pom.xml"

                    docker build                       --pull                       -t "$BACKEND_IMAGE"                       "$SERVICE_DIR"

                    docker image inspect "$BACKEND_IMAGE" >/dev/null

                    echo "DOCKER BUILD - FRONTEND"

                    test -f "$FRONTEND_DIR/Dockerfile"
                    test -f "$FRONTEND_DIR/package.json"
                    test -d "$FRONTEND_DIR/dist"

                    docker build                       --pull                       -t "$FRONTEND_IMAGE"                       "$FRONTEND_DIR"

                    docker image inspect "$FRONTEND_IMAGE" >/dev/null

                    echo "DOCKER IMAGES CREATED"

                    docker images "$BACKEND_IMAGE"
                    docker images "$FRONTEND_IMAGE"
                '''
            }
        }

        stage('Container Security - Trivy') {
            steps {
                sh '''
                    set -eux

                    echo "TRIVY USER-SERVICE IMAGE SCAN"

                    trivy image                       --scanners vuln,secret,misconfig                       --exit-code 1                       --severity CRITICAL,HIGH                       --ignore-unfixed                       --cache-dir "$TRIVY_CACHE_DIR"                       "$BACKEND_IMAGE"

                    echo "TRIVY FRONTEND IMAGE SCAN"

                    trivy image                       --scanners vuln,secret,misconfig                       --exit-code 1                       --severity CRITICAL,HIGH                       --ignore-unfixed                       --cache-dir "$TRIVY_CACHE_DIR"                       "$FRONTEND_IMAGE"
                '''
            }
        }

        stage('Container Sanity Test') {
            steps {
                sh '''
                    set -eux

                    echo "USER-SERVICE CONTAINER SANITY TEST"

                    docker image inspect "$BACKEND_IMAGE" >/dev/null

                    docker run                       --rm                       --entrypoint java                       "$BACKEND_IMAGE"                       -version

                    echo "FRONTEND CONTAINER SANITY TEST"

                    docker image inspect "$FRONTEND_IMAGE" >/dev/null

                    CONTAINER_NAME="ecommerce-frontend-sanity-${BUILD_NUMBER}"

                    docker run -d                       --name "$CONTAINER_NAME"                       -p 18080:8080                       "$FRONTEND_IMAGE"

                    trap 'docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true' EXIT

                    sleep 5

                    curl -fsS http://127.0.0.1:18080/ >/dev/null

                    echo "FRONTEND CONTAINER SANITY TEST PASSED"
                '''
            }
        }

        stage('ECR Push') {
            when {
                expression {
                    params.PUSH_ECR
                }
            }

            steps {
                sh '''
                    set -eux

                    : "${AWS_REGION:?AWS_REGION is required}"
                    : "${ECR_BACKEND_REPOSITORY:?ECR_BACKEND_REPOSITORY is required}"
                    : "${ECR_FRONTEND_REPOSITORY:?ECR_FRONTEND_REPOSITORY is required}"

                    ACCOUNT_ID=$(
                        aws sts get-caller-identity                           --query Account                           --output text
                    )

                    REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

                    echo "AWS Account : $ACCOUNT_ID"
                    echo "AWS Region  : $AWS_REGION"
                    echo "Registry    : $REGISTRY"

                    aws ecr describe-repositories                       --repository-names "$ECR_BACKEND_REPOSITORY"                       --region "$AWS_REGION"                       >/dev/null 2>&1                     ||                     aws ecr create-repository                       --repository-name "$ECR_BACKEND_REPOSITORY"                       --region "$AWS_REGION"                       >/dev/null

                    aws ecr describe-repositories                       --repository-names "$ECR_FRONTEND_REPOSITORY"                       --region "$AWS_REGION"                       >/dev/null 2>&1                     ||                     aws ecr create-repository                       --repository-name "$ECR_FRONTEND_REPOSITORY"                       --region "$AWS_REGION"                       >/dev/null

                    aws ecr get-login-password                       --region "$AWS_REGION"                     | docker login                       --username AWS                       --password-stdin "$REGISTRY"

                    docker tag                       "$BACKEND_IMAGE"                       "$REGISTRY/$ECR_BACKEND_REPOSITORY:$BUILD_NUMBER"

                    docker tag                       "$BACKEND_IMAGE"                       "$REGISTRY/$ECR_BACKEND_REPOSITORY:$GIT_SHA"

                    docker tag                       "$FRONTEND_IMAGE"                       "$REGISTRY/$ECR_FRONTEND_REPOSITORY:$BUILD_NUMBER"

                    docker tag                       "$FRONTEND_IMAGE"                       "$REGISTRY/$ECR_FRONTEND_REPOSITORY:$GIT_SHA"

                    docker push                       "$REGISTRY/$ECR_BACKEND_REPOSITORY:$BUILD_NUMBER"

                    docker push                       "$REGISTRY/$ECR_BACKEND_REPOSITORY:$GIT_SHA"

                    docker push                       "$REGISTRY/$ECR_FRONTEND_REPOSITORY:$BUILD_NUMBER"

                    docker push                       "$REGISTRY/$ECR_FRONTEND_REPOSITORY:$GIT_SHA"

                    echo "ECR PUSH COMPLETED"
                '''
            }
        }
    }

    post {
        always {
            sh '''
                echo "Cleaning local Docker images..."

                docker image rm "$BACKEND_IMAGE"                   >/dev/null 2>&1 || true

                docker image rm "$FRONTEND_IMAGE"                   >/dev/null 2>&1 || true
            '''

            archiveArtifacts(
                artifacts: 'ecommerce-app/services/user-service/target/*.jar,ecommerce-app/services/frontend/dist/**',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }

        success {
            echo '''
============================================================
PHASE 3.5 CI PIPELINE COMPLETED SUCCESSFULLY
============================================================
'''
        }

        failure {
            echo '''
============================================================
PHASE 3.5 CI PIPELINE FAILED
============================================================

Review the failed stage and security findings.

============================================================
'''
        }
    }
}

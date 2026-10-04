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

      string(
          name: 'SONAR_HOST_URL',
          defaultValue: 'http://3.221.55.212:9000',
          description: 'SonarQube server URL'
       )

        booleanParam(
            name: 'RUN_DEPENDENCY_CHECK',
            defaultValue: false,
            description: 'Run OWASP Dependency-Check. Downloads Maven plugin/data on first run.'
        )

        booleanParam(
            name: 'PUSH_ECR',
            defaultValue: false,
            description: 'Push immutable Docker images to AWS ECR. Requires AWS credentials on Jenkins agent.'
        )

        string(
            name: 'AWS_REGION',
            defaultValue: 'us-east-1',
            description: 'AWS region for ECR'
        )

        string(
            name: 'ECR_REPOSITORY',
            defaultValue: 'ecommerce/user-service',
            description: 'AWS ECR repository name'
        )
    }

    environment {

        /*
         * DevOps repository:
         * Checked out by Jenkins SCM.
         *
         * Application repository:
         * Checked out separately into ecommerce-app.
         */
        APP_DIR = 'ecommerce-app'

        /*
         * Current Phase 3.5 service.
         */
        SERVICE_DIR = 'ecommerce-app/services/user-service'

        /*
         * Docker image.
         */
        IMAGE_NAME = "ecommerce-user-service:${BUILD_NUMBER}"

        /*
         * Trivy cache.
         */
        TRIVY_CACHE_DIR = "${WORKSPACE}/.trivy-cache"
        SONAR_HOST_URL = 'http://3.221.55.212:9000'
    }

    stages {

        // ============================================================
        // 1. CHECKOUT DEVOPS + APPLICATION REPOSITORIES
        // ============================================================

        stage('Checkout') {
            steps {

                echo '============================================================'
                echo 'Checking out DevOps repository'
                echo '============================================================'

                checkout scm

                echo '============================================================'
                echo 'Checking out E-commerce application repository'
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

                echo '============================================================'
                echo 'Checkout completed'
                echo '============================================================'
            }
        }


        // ============================================================
        // 2. WORKSPACE INFORMATION
        // ============================================================

        stage('Workspace Info') {
            steps {

                sh '''
                    set -eux

                    echo "============================================================"
                    echo "SYSTEM INFORMATION"
                    echo "============================================================"

                    echo "JAVA"
                    java -version

                    echo
                    echo "MAVEN"
                    mvn -version

                    echo
                    echo "NODE"
                    node --version

                    echo
                    echo "NPM"
                    npm --version

                    echo
                    echo "DOCKER"
                    docker --version

                    echo
                    echo "AWS CLI"
                    aws --version

                    echo
                    echo "TRIVY"
                    trivy --version

                    echo
                    echo "SEMGREP"
                    semgrep --version

                    echo
                    echo "CHECKOV"
                    checkov --version

                    echo
                    echo "============================================================"
                    echo "WORKSPACE"
                    echo "============================================================"

                    pwd

                    echo
                    echo "Top-level workspace:"
                    ls -la

                    echo
                    echo "Application directory:"
                    ls -la "$APP_DIR"

                    echo
                    echo "Service directory:"
                    ls -la "$SERVICE_DIR"

                    echo
                    echo "============================================================"
                    echo "VALIDATING MAVEN PROJECT"
                    echo "============================================================"

                    test -f "$SERVICE_DIR/pom.xml"

                    echo "Maven POM found:"
                    ls -lh "$SERVICE_DIR/pom.xml"

                    echo
                    echo "============================================================"
                    echo "VALIDATING DOCKERFILE"
                    echo "============================================================"

                    test -f "$SERVICE_DIR/Dockerfile"

                    echo "Dockerfile found:"
                    ls -lh "$SERVICE_DIR/Dockerfile"

                    echo
                    echo "============================================================"
                    echo "APPLICATION GIT COMMIT"
                    echo "============================================================"

                    git -C "$APP_DIR" rev-parse --short HEAD
                '''
            }
        }


        // ============================================================
        // 3. MAVEN BUILD
        // ============================================================

        stage('Maven Build & Unit Test') {
            steps {

                dir(env.SERVICE_DIR) {

                    sh '''
                        set -eux

                        echo "============================================================"
                        echo "MAVEN BUILD & UNIT TEST"
                        echo "============================================================"

                        echo "Service directory:"
                        pwd

                        echo
                        echo "Maven version:"
                        mvn -version

                        echo
                        echo "Maven POM:"
                        ls -lh pom.xml

                        echo
                        echo "Running Maven clean verify..."

                        mvn -B -ntp clean verify

                        echo
                        echo "============================================================"
                        echo "MAVEN BUILD SUCCESSFUL"
                        echo "============================================================"

                        echo
                        echo "Generated JAR files:"

                        find target \
                          -maxdepth 2 \
                          -type f \
                          -name '*.jar' \
                          -print
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


        // ============================================================
        // 4. FRONTEND BUILD
        // ============================================================

        stage('Frontend Build') {
            steps {

                script {

                    def frontendExists = fileExists(
                        "${env.APP_DIR}/frontend/package.json"
                    )

                    if (frontendExists) {

                        dir("${env.APP_DIR}/frontend") {

                            sh '''
                                set -eux

                                echo "============================================================"
                                echo "FRONTEND NPM INSTALL"
                                echo "============================================================"

                                npm install --no-audit --no-fund

                                echo
                                echo "============================================================"
                                echo "FRONTEND BUILD"
                                echo "============================================================"

                                npm run build
                            '''
                        }

                    } else {

                        echo 'Frontend directory/package.json not found.'
                        echo 'Frontend build is skipped for this Phase 3.5 service build.'
                    }
                }
            }
        }


        // ============================================================
        // 5. STATIC SECURITY - SEMGREP
        // ============================================================

        stage('Static Security - Semgrep') {
            steps {

                sh '''
                    set -eux

                    echo "============================================================"
                    echo "SEMGREP SECURITY SCAN"
                    echo "============================================================"

                    semgrep scan \
                      --config p/java \
                      --config p/typescript \
                      --error \
                      --exclude node_modules \
                      --exclude target \
                      --exclude .trivy-cache \
                      .
                '''
            }
        }


        // ============================================================
        // 6. FILESYSTEM SECURITY - TRIVY
        // ============================================================

        stage('Filesystem Security - Trivy') {
            steps {

                sh '''
                    set -eux

                    echo "============================================================"
                    echo "TRIVY FILESYSTEM SECURITY SCAN"
                    echo "============================================================"

                    mkdir -p "$TRIVY_CACHE_DIR"

                    trivy fs \
                      --scanners vuln,secret,misconfig \
                      --exit-code 1 \
                      --severity CRITICAL,HIGH \
                      --ignore-unfixed \
                      --cache-dir "$TRIVY_CACHE_DIR" \
                      .
                '''
            }
        }
     


        // ============================================================
        // 8. DEPENDENCY SECURITY - OWASP
        // ============================================================

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

                        echo "============================================================"
                        echo "OWASP DEPENDENCY CHECK"
                        echo "============================================================"

                        mvn -B -ntp \
                          -DskipTests \
                          org.owasp:dependency-check-maven:check \
                          -DfailBuildOnCVSS=7
                    '''
                }
            }
        }


        // ============================================================
        // 9. SONARQUBE
        // ============================================================

        stage('SonarQube') {

            when {
                expression {
                    params.RUN_SONAR
                }
            }

            steps {

                withCredentials([
                    string(
                        credentialsId: 'sonar-token',
                        variable: 'SONAR_TOKEN'
                    )
                ]) {

                    sh '''
                        set -eux

                        echo "============================================================"
                        echo "SONARQUBE ANALYSIS"
                        echo "============================================================"

                        : "${SONAR_HOST_URL:?SONAR_HOST_URL is required}"

                        mvn -B -ntp \
                          -f "$SERVICE_DIR/pom.xml" \
                          -DskipTests \
                          -Dsonar.projectKey=ecommerce-user-service \
                          -Dsonar.projectName=ecommerce-user-service \
                          -Dsonar.host.url="$SONAR_HOST_URL" \
                          -Dsonar.token="$SONAR_TOKEN" \
                          sonar:sonar
                    '''

                    sh '''
                        set -eu

                        echo "============================================================"
                        echo "SONARQUBE QUALITY GATE"
                        echo "============================================================"

                        : "${SONAR_HOST_URL:?SONAR_HOST_URL is required}"

                        for i in $(seq 1 30); do

                            STATUS=$(
                                curl -sf \
                                  -u "$SONAR_TOKEN:" \
                                  "$SONAR_HOST_URL/api/qualitygates/project_status?projectKey=ecommerce-user-service" \
                                | python3 -c '
import json
import sys

data = json.load(sys.stdin)

print(
    data.get(
        "projectStatus",
        {}
    ).get(
        "status",
        "PENDING"
    )
)
'
                            ) || STATUS=PENDING

                            echo "Quality Gate status: $STATUS"

                            if [ "$STATUS" = "OK" ]; then
                                exit 0
                            fi

                            if [ "$STATUS" = "ERROR" ]; then
                                exit 1
                            fi

                            sleep 10

                        done

                        echo "SonarQube Quality Gate did not finish in expected time."

                        exit 1
                    '''
                }
            }
        }


        // ============================================================
        // 10. DOCKER BUILD
        // ============================================================

        stage('Docker Build') {
            steps {

                script {

                    env.GIT_SHA = sh(
                        script: 'git -C "$SERVICE_DIR" rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    env.GIT_SHORT_SHA = sh(
                        script: 'git -C "$SERVICE_DIR" rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }

                sh '''
                    set -eux

                    echo "============================================================"
                    echo "DOCKER BUILD"
                    echo "============================================================"

                    echo "Service directory : $SERVICE_DIR"
                    echo "Docker image      : $IMAGE_NAME"
                    echo "Git SHA           : $GIT_SHA"

                    test -f "$SERVICE_DIR/Dockerfile"

                    docker build \
                      --pull \
                      -t "$IMAGE_NAME" \
                      "$SERVICE_DIR"

                    echo
                    echo "Docker image created successfully:"

                    docker image inspect "$IMAGE_NAME" >/dev/null

                    docker images "$IMAGE_NAME"
                '''
            }
        }


        // ============================================================
        // 11. CONTAINER SECURITY - TRIVY
        // ============================================================

        stage('Container Security - Trivy') {
            steps {

                sh '''
                    set -eux

                    echo "============================================================"
                    echo "TRIVY CONTAINER SECURITY SCAN"
                    echo "============================================================"

                    trivy image \
                      --scanners vuln,secret,misconfig \
                      --exit-code 1 \
                      --severity CRITICAL,HIGH \
                      --ignore-unfixed \
                      --cache-dir "$TRIVY_CACHE_DIR" \
                      "$IMAGE_NAME"
                '''
            }
        }


        // ============================================================
        // 12. ECR PUSH
        // ============================================================

        stage('ECR Push') {

            when {
                expression {
                    params.PUSH_ECR
                }
            }

            steps {

                sh '''
                    set -eux

                    echo "============================================================"
                    echo "AWS ECR PUSH"
                    echo "============================================================"

                    : "${AWS_REGION:?AWS_REGION is required}"
                    : "${ECR_REPOSITORY:?ECR_REPOSITORY is required}"

                    ACCOUNT_ID=$(
                        aws sts get-caller-identity \
                          --query Account \
                          --output text
                    )

                    REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

                    echo "AWS Account : $ACCOUNT_ID"
                    echo "AWS Region  : $AWS_REGION"
                    echo "Registry    : $REGISTRY"
                    echo "Repository  : $ECR_REPOSITORY"

                    aws ecr describe-repositories \
                      --repository-names "$ECR_REPOSITORY" \
                      --region "$AWS_REGION" \
                      >/dev/null 2>&1 \
                    || \
                    aws ecr create-repository \
                      --repository-name "$ECR_REPOSITORY" \
                      --region "$AWS_REGION" \
                      >/dev/null

                    echo "Logging in to ECR..."

                    aws ecr get-login-password \
                      --region "$AWS_REGION" \
                    | docker login \
                      --username AWS \
                      --password-stdin "$REGISTRY"

                    echo "Tagging Docker image..."

                    docker tag \
                      "$IMAGE_NAME" \
                      "$REGISTRY/$ECR_REPOSITORY:$BUILD_NUMBER"

                    docker tag \
                      "$IMAGE_NAME" \
                      "$REGISTRY/$ECR_REPOSITORY:$GIT_SHA"

                    echo "Pushing BUILD_NUMBER tag..."

                    docker push \
                      "$REGISTRY/$ECR_REPOSITORY:$BUILD_NUMBER"

                    echo "Pushing Git SHA tag..."

                    docker push \
                      "$REGISTRY/$ECR_REPOSITORY:$GIT_SHA"

                    echo
                    echo "============================================================"
                    echo "ECR PUSH COMPLETED"
                    echo "============================================================"

                    echo "Image:"
                    echo "$REGISTRY/$ECR_REPOSITORY:$BUILD_NUMBER"

                    echo "Image:"
                    echo "$REGISTRY/$ECR_REPOSITORY:$GIT_SHA"
                '''
            }
        }


        // ============================================================
        // 13. CONTAINER SANITY TEST
        // ============================================================

        stage('Container Sanity Test') {
            steps {

                sh '''
                    set -eux

                    echo "============================================================"
                    echo "CONTAINER SANITY TEST"
                    echo "============================================================"

                    echo "Testing Java runtime inside container..."

                    docker run \
                      --rm \
                      --entrypoint java \
                      "$IMAGE_NAME" \
                      -version

                    echo "Inspecting Docker image..."

                    docker image inspect "$IMAGE_NAME" >/dev/null

                    echo
                    echo "Container sanity test passed."
                '''
            }
        }
    }


    // ================================================================
    // POST ACTIONS
    // ================================================================

    post {

        always {

            sh '''
                docker image rm "$IMAGE_NAME" \
                  >/dev/null 2>&1 || true
            '''

            archiveArtifacts(
                artifacts: 'ecommerce-app/services/user-service/target/*.jar,ecommerce-app/frontend/dist/**',
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

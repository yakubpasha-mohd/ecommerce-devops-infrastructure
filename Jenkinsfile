pipeline {

    agent any


    // ============================================================
    // PIPELINE OPTIONS
    // ============================================================

    options {

        timestamps()

        ansiColor('xterm')

        disableConcurrentBuilds()

        buildDiscarder(
            logRotator(
                numToKeepStr: '20'
            )
        )
    }


    // ============================================================
    // PARAMETERS
    // ============================================================

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
            description: 'Push Docker image to AWS ECR'
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


    // ============================================================
    // ENVIRONMENT
    // ============================================================

    environment {

        APP_DIR = 'ecommerce-app'

        SERVICE_DIR = 'ecommerce-app/services/user-service'

        FRONTEND_DIR = 'ecommerce-app/frontend'

        IMAGE_NAME = "ecommerce-application:${BUILD_NUMBER}"

        TRIVY_CACHE_DIR = "${WORKSPACE}/.trivy-cache"
    }


    // ============================================================
    // STAGES
    // ============================================================

    stages {


        // ========================================================
        // 1. CHECKOUT
        // ========================================================

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


                echo '============================================================'
                echo 'CHECKOUT COMPLETED'
                echo '============================================================'
            }
        }


        // ========================================================
        // 2. WORKSPACE INFORMATION
        // ========================================================

        stage('Workspace Info') {

            steps {

                sh '''
                    set -eux

                    echo "============================================================"
                    echo "SYSTEM INFORMATION"
                    echo "============================================================"

                    echo
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

                    ls -la


                    echo
                    echo "============================================================"
                    echo "APPLICATION DIRECTORY"
                    echo "============================================================"

                    ls -la "$APP_DIR"


                    echo
                    echo "============================================================"
                    echo "FRONTEND DIRECTORY"
                    echo "============================================================"

                    test -d "$FRONTEND_DIR"

                    ls -la "$FRONTEND_DIR"

                    test -f "$FRONTEND_DIR/package.json"


                    echo
                    echo "============================================================"
                    echo "BACKEND SERVICE DIRECTORY"
                    echo "============================================================"

                    test -d "$SERVICE_DIR"

                    ls -la "$SERVICE_DIR"

                    test -f "$SERVICE_DIR/pom.xml"


                    echo
                    echo "============================================================"
                    echo "COMBINED DOCKERFILE"
                    echo "============================================================"

                    test -f "$APP_DIR/Dockerfile"

                    ls -lh "$APP_DIR/Dockerfile"


                    echo
                    echo "============================================================"
                    echo "APPLICATION GIT COMMIT"
                    echo "============================================================"

                    git -C "$APP_DIR" rev-parse HEAD
                '''
            }
        }


        // ========================================================
        // 3. MAVEN BUILD & UNIT TEST
        // ========================================================

        stage('Maven Build & Unit Test') {

            steps {

                dir(env.SERVICE_DIR) {

                    sh '''
                        set -eux

                        echo "============================================================"
                        echo "MAVEN BUILD & UNIT TEST"
                        echo "============================================================"

                        mvn -B -ntp clean verify


                        echo
                        echo "============================================================"
                        echo "MAVEN BUILD SUCCESSFUL"
                        echo "============================================================"


                        echo
                        echo "GENERATED JAR FILES"

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


        // ========================================================
        // 4. FRONTEND BUILD
        // ========================================================

        stage('Frontend Build') {

            steps {

                dir(env.FRONTEND_DIR) {

                    sh '''
                        set -eux

                        echo "============================================================"
                        echo "FRONTEND BUILD"
                        echo "============================================================"

                        echo "Frontend directory:"
                        pwd


                        echo
                        echo "package.json:"
                        test -f package.json
                        ls -lh package.json


                        echo
                        echo "Installing frontend dependencies..."


                        npm install \
                          --no-audit \
                          --no-fund


                        echo
                        echo "============================================================"
                        echo "RUNNING REACT BUILD"
                        echo "============================================================"


                        npm run build


                        echo
                        echo "============================================================"
                        echo "FRONTEND BUILD COMPLETED"
                        echo "============================================================"


                        test -d dist


                        echo
                        echo "Frontend build output:"

                        ls -lah dist


                        echo
                        echo "Frontend files:"

                        find dist \
                          -maxdepth 2 \
                          -type f \
                          -print
                    '''
                }
            }
        }


        // ========================================================
        // 5. STATIC SECURITY - SEMGREP
        // ========================================================

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
                      --exclude dist \
                      --exclude .trivy-cache \
                      .
                '''
            }
        }


        // ========================================================
        // 6. FILESYSTEM SECURITY - TRIVY
        // ========================================================

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


        // ========================================================
        // 7. DEPENDENCY SECURITY - OWASP
        // ========================================================

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


        // ========================================================
        // 8. SONARQUBE
        // ========================================================

        stage('SonarQube') {

            steps {

                echo '============================================================'
                echo 'SONARQUBE CODE ANALYSIS'
                echo '============================================================'


                withCredentials([

                    string(
                        credentialsId: 'sonar-token',
                        variable: 'SONAR_TOKEN'
                    )

                ]) {


                    withSonarQubeEnv('SonarQube') {

                        sh '''
                            set -eux

                            echo "============================================================"
                            echo "SONARQUBE ANALYSIS"
                            echo "============================================================"

                            echo "SonarQube URL: $SONAR_HOST_URL"

                            echo "Project Key: ecommerce-user-service"


                            test -f "$SERVICE_DIR/pom.xml"


                            mvn -B -ntp \
                              -f "$SERVICE_DIR/pom.xml" \
                              -DskipTests \
                              -Dsonar.projectKey=ecommerce-user-service \
                              -Dsonar.projectName=ecommerce-user-service \
                              -Dsonar.host.url="$SONAR_HOST_URL" \
                              -Dsonar.token="$SONAR_TOKEN" \
                              org.sonarsource.scanner.maven:sonar-maven-plugin:sonar


                            echo
                            echo "============================================================"
                            echo "SONARQUBE ANALYSIS SUBMITTED"
                            echo "============================================================"
                        '''
                    }


                    echo '============================================================'
                    echo 'WAITING FOR SONARQUBE QUALITY GATE'
                    echo '============================================================'


                    timeout(
                        time: 10,
                        unit: 'MINUTES'
                    ) {

                        script {

                            def qualityGate = waitForQualityGate(
                                abortPipeline: false
                            )


                            echo '============================================================'
                            echo "SONARQUBE QUALITY GATE STATUS: ${qualityGate.status}"
                            echo '============================================================'


                            if (qualityGate.status == 'OK') {

                                echo '============================================================'
                                echo 'SONARQUBE QUALITY GATE PASSED'
                                echo '============================================================'

                            } else {

                                echo '============================================================'
                                echo "SONARQUBE QUALITY GATE FAILED"
                                echo "STATUS: ${qualityGate.status}"
                                echo '============================================================'


                                error(
                                    "SonarQube Quality Gate failed: ${qualityGate.status}"
                                )
                            }
                        }
                    }
                }
            }
        }


        // ========================================================
        // 9. DOCKER BUILD - FRONTEND + BACKEND
        // ========================================================

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

                    echo "============================================================"
                    echo "DOCKER BUILD - FRONTEND + BACKEND"
                    echo "============================================================"


                    echo "Application directory : $APP_DIR"

                    echo "Frontend directory    : $FRONTEND_DIR"

                    echo "Backend directory     : $SERVICE_DIR"

                    echo "Docker image          : $IMAGE_NAME"

                    echo "Git SHA               : $GIT_SHA"


                    echo
                    echo "============================================================"
                    echo "VALIDATING DOCKER BUILD CONTEXT"
                    echo "============================================================"


                    test -f "$APP_DIR/Dockerfile"

                    test -f "$FRONTEND_DIR/package.json"

                    test -d "$FRONTEND_DIR/dist"

                    test -f "$SERVICE_DIR/pom.xml"


                    echo
                    echo "Frontend build output:"
                    du -sh "$FRONTEND_DIR/dist"


                    echo
                    echo "============================================================"
                    echo "BUILDING COMBINED DOCKER IMAGE"
                    echo "============================================================"


                    docker build \
                      --pull \
                      -t "$IMAGE_NAME" \
                      "$APP_DIR"


                    echo
                    echo "============================================================"
                    echo "DOCKER IMAGE CREATED"
                    echo "============================================================"


                    docker image inspect "$IMAGE_NAME" >/dev/null


                    docker images "$IMAGE_NAME"
                '''
            }
        }


        // ========================================================
        // 10. CONTAINER SECURITY - TRIVY
        // ========================================================

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


        // ========================================================
        // 11. ECR PUSH
        // ========================================================

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


                    echo
                    echo "Checking ECR repository..."


                    aws ecr describe-repositories \
                      --repository-names "$ECR_REPOSITORY" \
                      --region "$AWS_REGION" \
                      >/dev/null 2>&1 \
                    || \
                    aws ecr create-repository \
                      --repository-name "$ECR_REPOSITORY" \
                      --region "$AWS_REGION" \
                      >/dev/null


                    echo
                    echo "Logging in to ECR..."


                    aws ecr get-login-password \
                      --region "$AWS_REGION" \
                    | docker login \
                      --username AWS \
                      --password-stdin "$REGISTRY"


                    echo
                    echo "Tagging Docker image..."


                    docker tag \
                      "$IMAGE_NAME" \
                      "$REGISTRY/$ECR_REPOSITORY:$BUILD_NUMBER"


                    docker tag \
                      "$IMAGE_NAME" \
                      "$REGISTRY/$ECR_REPOSITORY:$GIT_SHA"


                    echo
                    echo "Pushing BUILD_NUMBER tag..."


                    docker push \
                      "$REGISTRY/$ECR_REPOSITORY:$BUILD_NUMBER"


                    echo
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


        // ========================================================
        // 12. CONTAINER SANITY TEST
        // ========================================================

        stage('Container Sanity Test') {

            steps {

                sh '''
                    set -eux

                    echo "============================================================"
                    echo "CONTAINER SANITY TEST"
                    echo "============================================================"


                    echo
                    echo "Checking Docker image..."


                    docker image inspect "$IMAGE_NAME" >/dev/null


                    echo
                    echo "Testing Java runtime inside container..."


                    docker run \
                      --rm \
                      --entrypoint java \
                      "$IMAGE_NAME" \
                      -version


                    echo
                    echo "============================================================"
                    echo "CONTAINER SANITY TEST PASSED"
                    echo "============================================================"
                '''
            }
        }
    }


    // ============================================================
    // POST ACTIONS
    // ============================================================

    post {

        always {

            sh '''
                echo "Cleaning local Docker image..."

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

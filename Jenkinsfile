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
            name: 'ECR_BACKEND_REPOSITORY',
            defaultValue: 'ecommerce/user-service',
            description: 'AWS ECR repository for the user-service Docker image'
        )

        string(
            name: 'ECR_FRONTEND_REPOSITORY',
            defaultValue: 'ecommerce/frontend',
            description: 'AWS ECR repository for the frontend Docker image'
        )
    }


    // ============================================================
    // ENVIRONMENT
    // ============================================================

      environment {
    APP_DIR = 'ecommerce-app'
    SERVICE_DIR = 'ecommerce-app/services/user-service'
    FRONTEND_DIR = 'ecommerce-app/services/frontend'

    BACKEND_IMAGE = "ecommerce-user-service:${BUILD_NUMBER}"
    FRONTEND_IMAGE = "ecommerce-frontend:${BUILD_NUMBER}"

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

            sh '''
                echo "Cleaning local Docker images..."

                docker image rm "$BACKEND_IMAGE" \
                  >/dev/null 2>&1 || true

                docker image rm "$FRONTEND_IMAGE" \
                  >/dev/null 2>&1 || true

                docker image rm "$REGISTRY/$ECR_BACKEND_REPOSITORY:$BUILD_NUMBER" \
                  >/dev/null 2>&1 || true

                docker image rm "$REGISTRY/$ECR_BACKEND_REPOSITORY:$GIT_SHA" \
                  >/dev/null 2>&1 || true

                docker image rm "$REGISTRY/$ECR_FRONTEND_REPOSITORY:$BUILD_NUMBER" \
                  >/dev/null 2>&1 || true

                docker image rm "$REGISTRY/$ECR_FRONTEND_REPOSITORY:$GIT_SHA" \
                  >/dev/null 2>&1 || true
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

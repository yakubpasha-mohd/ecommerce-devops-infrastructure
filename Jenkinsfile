pipeline {
    agent any

    options {
        timestamps()
        ansiColor('xterm')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        choice(name: 'SERVICE', choices: ['user-service'], description: 'Microservice to build in Phase 3.5')
        booleanParam(name: 'RUN_SONAR', defaultValue: false, description: 'Run SonarQube analysis. Requires sonar-token credential and SONAR_HOST_URL.')
        booleanParam(name: 'RUN_DEPENDENCY_CHECK', defaultValue: false, description: 'Run OWASP Dependency-Check. Downloads Maven plugin/data on first run.')
        booleanParam(name: 'PUSH_ECR', defaultValue: false, description: 'Push immutable Docker images to AWS ECR. Requires AWS credentials on the Jenkins agent.')
        string(name: 'AWS_REGION', defaultValue: 'us-east-1', description: 'AWS region for ECR')
        string(name: 'ECR_REPOSITORY', defaultValue: 'ecommerce/user-service', description: 'ECR repository name')
    }

    environment {
        SERVICE_DIR = 'services/user-service'
        IMAGE_NAME = "ecommerce-user-service:${BUILD_NUMBER}"
        TRIVY_CACHE_DIR = "${WORKSPACE}/.trivy-cache"
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Workspace Info') {
            steps {
                sh '''
                    set -eux
                    java -version
                    mvn -version
                    node --version
                    npm --version
                    docker --version
                    aws --version
                    trivy --version
                    semgrep --version
                    checkov --version
                '''
            }
        }

        stage('Backend Unit Test') {
            steps {
                dir(env.SERVICE_DIR) {
                    sh 'mvn -B -ntp clean test'
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'services/user-service/target/surefire-reports/*.xml'
                }
            }
        }

        stage('Frontend Build') {
            steps {
                dir('frontend') {
                    sh 'npm install --no-audit --no-fund'
                    sh 'npm run build'
                }
            }
        }

        stage('Static Security - Semgrep') {
            steps {
                sh '''
                    set -eux
                    semgrep scan --config p/java --config p/typescript --error --exclude node_modules --exclude target .
                '''
            }
        }

        stage('Filesystem Security - Trivy') {
            steps {
                sh '''
                    set -eux
                    mkdir -p "$TRIVY_CACHE_DIR"
                    trivy fs --scanners vuln,secret,misconfig --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed --cache-dir "$TRIVY_CACHE_DIR" .
                '''
            }
        }

        stage('IaC Security - Checkov') {
            steps {
                sh '''
                    set -eux
                    if find infrastructure -type f \( -name '*.tf' -o -name '*.tf.json' -o -name '*.yaml' -o -name '*.yml' \) | grep -q .; then
                      checkov -d infrastructure --quiet --compact
                    else
                      echo 'No Terraform/IaC files found in infrastructure yet; Checkov stage is informational.'
                    fi
                '''
            }
        }

        stage('Dependency Security - OWASP') {
            when { expression { params.RUN_DEPENDENCY_CHECK } }
            steps {
                dir(env.SERVICE_DIR) {
                    sh 'mvn -B -ntp -DskipTests org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7'
                }
            }
        }

        stage('SonarQube') {
            when { expression { params.RUN_SONAR } }
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        set -eux
                        mvn -B -ntp -f "$SERVICE_DIR/pom.xml" \
                          -DskipTests \
                          -Dsonar.projectKey=ecommerce-user-service \
                          -Dsonar.projectName=ecommerce-user-service \
                          -Dsonar.host.url="$SONAR_HOST_URL" \
                          -Dsonar.token="$SONAR_TOKEN" \
                          sonar:sonar
                    '''
                    sh '''
                        set -eu
                        for i in $(seq 1 30); do
                          STATUS=$(curl -sf -u "$SONAR_TOKEN:" "$SONAR_HOST_URL/api/qualitygates/project_status?projectKey=ecommerce-user-service" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("projectStatus",{}).get("status","PENDING"))') || STATUS=PENDING
                          echo "Quality Gate status: $STATUS"
                          [ "$STATUS" = "OK" ] && exit 0
                          [ "$STATUS" = "ERROR" ] && exit 1
                          sleep 10
                        done
                        echo 'SonarQube Quality Gate did not finish in the expected time.'
                        exit 1
                    '''
                }
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    env.GIT_SHA = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                }
                sh '''
                    set -eux
                    docker build --pull -t "$IMAGE_NAME" "$SERVICE_DIR"
                '''
            }
        }

        stage('Container Security - Trivy') {
            steps {
                sh '''
                    set -eux
                    trivy image --scanners vuln,secret,misconfig --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed --cache-dir "$TRIVY_CACHE_DIR" "$IMAGE_NAME"
                '''
            }
        }

        stage('ECR Push') {
            when { expression { params.PUSH_ECR } }
            steps {
                sh '''
                    set -eux
                    : "${AWS_REGION:?AWS_REGION is required}"
                    : "${ECR_REPOSITORY:?ECR_REPOSITORY is required}"
                    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
                    REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
                    aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" >/dev/null 2>&1 || \
                      aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION" >/dev/null
                    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REGISTRY"
                    docker tag "$IMAGE_NAME" "$REGISTRY/$ECR_REPOSITORY:$BUILD_NUMBER"
                    docker tag "$IMAGE_NAME" "$REGISTRY/$ECR_REPOSITORY:$GIT_SHA"
                    docker push "$REGISTRY/$ECR_REPOSITORY:$BUILD_NUMBER"
                    docker push "$REGISTRY/$ECR_REPOSITORY:$GIT_SHA"
                    echo "Pushed immutable tags: $BUILD_NUMBER and $GIT_SHA"
                '''
            }
        }

        stage('Container Sanity Test') {
            steps {
                sh '''
                    set -eux
                    docker run --rm --entrypoint java "$IMAGE_NAME" -version
                    docker image inspect "$IMAGE_NAME" >/dev/null
                '''
            }
        }
    }

    post {
        always {
            sh 'docker image rm "$IMAGE_NAME" >/dev/null 2>&1 || true'
            archiveArtifacts artifacts: 'services/user-service/target/*.jar, frontend/dist/**', allowEmptyArchive: true, fingerprint: true
        }
        success { echo 'Phase 3.5 CI pipeline completed successfully.' }
        failure { echo 'Phase 3.5 CI pipeline failed. Review the failed stage and security findings.' }
    }
}

# Phase 3.5 — DevOps CI Foundation

This phase adds a reusable CI foundation around the working Phase 3 User Service.

## Included

- Root Jenkinsfile
- Jenkins Docker image with Docker CLI, AWS CLI, Node.js 22, Trivy, Semgrep and Checkov
- Jenkins Docker Compose bootstrap
- SonarQube Docker Compose bootstrap
- Maven/JUnit backend tests
- React production build
- Semgrep SAST
- Trivy filesystem and container image scanning
- Checkov IaC scanning when Terraform/IaC files are present
- Optional OWASP Dependency-Check hook
- Optional SonarQube analysis + Quality Gate polling
- Optional AWS ECR push with immutable build-number and Git-SHA tags
- Local CI helper script

## Jenkins bootstrap

```bash
cd devops/jenkins
docker compose up -d --build
```

Jenkins is exposed on port `8080`.

The Jenkins container uses the host Docker socket so the pipeline can build and scan images. For a production Jenkins installation, replace this with dedicated ephemeral build agents or a managed CI runner.

## SonarQube bootstrap

```bash
cd devops/sonar
docker compose up -d
```

SonarQube is exposed on port `9000`.

Create a Jenkins secret-text credential named:

```text
sonar-token
```

Set the Jenkins global environment variable:

```text
SONAR_HOST_URL=http://<sonarqube-host>:9000
```

Then run the pipeline with `RUN_SONAR=true`.

## ECR

The pipeline creates the ECR repository if it does not already exist and pushes:

```text
<build-number>
<git-commit-sha>
```

Do not use `latest` as the deployment identifier. Promote the immutable image tag between environments without rebuilding it.

The Jenkins agent needs AWS permissions for:

- sts:GetCallerIdentity
- ecr:DescribeRepositories
- ecr:CreateRepository
- ecr:GetAuthorizationToken
- ecr:BatchCheckLayerAvailability
- ecr:InitiateLayerUpload
- ecr:UploadLayerPart
- ecr:CompleteLayerUpload
- ecr:PutImage

Use Jenkins credentials/instance roles rather than storing AWS keys in the repository.

## Pipeline parameters

- `SERVICE`: current value `user-service`; extend this list as services are added.
- `RUN_SONAR`: enable after SonarQube is configured.
- `RUN_DEPENDENCY_CHECK`: enable when Maven Dependency-Check is required in the Jenkins environment.
- `PUSH_ECR`: enable when AWS/ECR credentials are configured.
- `AWS_REGION`: defaults to `us-east-1`.
- `ECR_REPOSITORY`: defaults to `ecommerce/user-service`.

## CI order

```text
Checkout
  -> Backend Unit Test
  -> Frontend Build
  -> Semgrep
  -> Trivy FS
  -> Checkov
  -> SonarQube + Quality Gate (optional)
  -> Docker Build
  -> Trivy Image
  -> ECR Push (optional)
  -> Container Smoke Test
```

## Next phase

Phase 3.5 intentionally stops at CI and image publication. Kubernetes/EKS deployment, Helm, GitOps, promotion and production CD belong to the next DevOps phase.

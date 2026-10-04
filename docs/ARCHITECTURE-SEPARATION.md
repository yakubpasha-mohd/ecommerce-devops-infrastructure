# Application vs DevOps/Infrastructure Separation

## Application repository/package

Owns business/application runtime:

- frontend
- microservices
- application tests
- database migrations
- application Dockerfiles
- local runtime Compose
- runtime database initialization

## DevOps/Infrastructure repository/package

Owns delivery/platform automation:

- Jenkins
- SonarQube
- Semgrep
- Trivy
- Checkov
- OWASP dependency scanning
- CI scripts
- quality/security gates
- ECR publishing
- future Terraform
- future Kubernetes/Helm
- future EKS deployment

## Target enterprise structure

```text
ecommerce-application/
  frontend/
  services/
  runtime-infrastructure/
  docker-compose.yml

 ecommerce-devops-infrastructure/
  jenkins/
  sonar/
  security/
  scripts/
  terraform/
  kubernetes/
  helm/
  docs/
```

The two packages can evolve independently.

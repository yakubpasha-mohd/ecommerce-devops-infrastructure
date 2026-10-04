# E-Commerce DevOps & Infrastructure — Phase 3.5

This package contains the **DevOps/CI foundation** and is intentionally separated from application source code.

## Included

- Jenkins pipeline (`Jenkinsfile`)
- Jenkins Docker setup and plugins
- SonarQube Docker setup
- Trivy security configuration
- CI helper scripts
- Phase 3.5 CI documentation
- Infrastructure/CI boundary documentation

## Application package

The application source is in the companion package:
`ecommerce-application-phase3.5`

It contains React, Spring Boot User Service, PostgreSQL runtime initialization, Dockerfiles, and application Docker Compose.

## CI flow

```text
Git checkout
   -> Maven test/build
   -> React build
   -> Semgrep
   -> Trivy filesystem scan
   -> Checkov
   -> OWASP dependency scan
   -> SonarQube quality gate
   -> Docker build
   -> Trivy image scan
   -> Optional AWS ECR push
```

## Important

This phase is CI-focused. EKS deployment/continuous delivery belongs to Phase 3.6.

## Jenkins

Start the Jenkins environment:

```bash
docker compose -f devops/jenkins/docker-compose.yml up -d --build
```

## SonarQube

Start SonarQube:

```bash
docker compose -f devops/sonar/docker-compose.yml up -d
```

## Separation principle

Application teams own:

- source code
- unit tests
- application Dockerfiles
- application runtime configuration

DevOps/platform teams own:

- Jenkins
- CI/CD pipelines
- quality gates
- security scanning
- image publishing
- deployment automation
- infrastructure automation

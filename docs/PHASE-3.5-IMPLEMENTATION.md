# Phase 3.5 Implementation — DevOps CI Foundation

## Scope

Phase 3.5 converts the working Phase 3 application into a CI-ready repository. The first service is `user-service`; the design is intended to be extended to the other eight microservices without changing the overall pipeline architecture.

## Acceptance matrix

| Capability | Status | Implementation |
|---|---|---|
| Jenkins pipeline | Implemented | `/Jenkinsfile` |
| Java/Maven unit tests | Implemented | `mvn clean test` |
| React build | Implemented | `npm install && npm run build` |
| Semgrep SAST | Implemented | Jenkins stage |
| Trivy filesystem scan | Implemented | Jenkins stage |
| Trivy container scan | Implemented | Jenkins stage |
| Checkov | Implemented | Conditional on IaC files |
| SonarQube | Implemented/optional | `RUN_SONAR=true` |
| Quality Gate | Implemented/optional | SonarQube API polling |
| ECR | Implemented/optional | `PUSH_ECR=true` |
| Immutable image tags | Implemented | build number + Git SHA |
| Jenkins bootstrap | Implemented | `devops/jenkins` |
| SonarQube bootstrap | Implemented | `devops/sonar` |
| EKS/CD | Deferred | Phase 4+ |

## Important security behavior

- No AWS keys are committed.
- No SonarQube token is committed.
- `trivyignore` is intentionally empty.
- ECR push is opt-in through a Jenkins parameter.
- Development JWT secrets remain development-only and must not be reused in production.

## First Jenkins run

1. Start Jenkins from `devops/jenkins`.
2. Create/configure the Pipeline job against the repository.
3. Ensure the Jenkins agent has label `docker`.
4. Verify Docker socket access.
5. Run with defaults first: SonarQube and ECR push disabled.
6. Configure SonarQube and `sonar-token`, then enable `RUN_SONAR`.
7. Configure AWS IAM/instance-role permissions, then enable `PUSH_ECR`.

## Extension pattern

When Catalog Service is introduced, add:

```text
services/catalog-service/
```

and extend the Jenkins service choice/repository mapping. The CI gates remain the same.

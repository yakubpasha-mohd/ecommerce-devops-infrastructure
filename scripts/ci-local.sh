#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

printf '\n== Backend tests ==\n'
(cd services/user-service && mvn -B -ntp clean test)

printf '\n== Frontend build ==\n'
(cd frontend && npm install --no-audit --no-fund && npm run build)

printf '\n== Semgrep ==\n'
semgrep scan --config p/java --config p/typescript --error --exclude node_modules --exclude target .

printf '\n== Trivy filesystem ==\n'
trivy fs --scanners vuln,secret,misconfig --severity CRITICAL,HIGH --ignore-unfixed .

printf '\nPhase 3.5 local CI checks completed.\n'

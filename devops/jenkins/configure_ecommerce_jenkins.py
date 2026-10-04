#!/usr/bin/env python3

import os
import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote

from dotenv import load_dotenv


# ============================================================
# LOAD .env
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")

if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)
    print(f"Loaded environment file: {ENV_FILE}")
else:
    print(f"WARNING: .env file not found: {ENV_FILE}")


# ============================================================
# CONFIGURATION
# ============================================================

JENKINS_URL = os.getenv(
    "JENKINS_URL",
    "http://localhost:8080"
).rstrip("/")

JENKINS_USER = os.getenv(
    "JENKINS_USER",
    "admin"
)

JENKINS_TOKEN = os.getenv(
    "JENKINS_TOKEN"
)

JOB_NAME = os.getenv(
    "JENKINS_JOB_NAME",
    "ecommerce-devops-infrastructure"
)

DEVOPS_REPO_URL = os.getenv(
    "DEVOPS_REPO_URL",
    ""
)

GIT_BRANCH = os.getenv(
    "GIT_BRANCH",
    "*/main"
)

GIT_CREDENTIALS_ID = os.getenv(
    "GIT_CREDENTIALS_ID",
    ""
)

JENKINSFILE_PATH = os.getenv(
    "JENKINSFILE_PATH",
    "Jenkinsfile"
)


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("E-COMMERCE JENKINS CONFIGURATION")
print("=" * 70)

print(f"Jenkins URL       : {JENKINS_URL}")
print(f"Jenkins user      : {JENKINS_USER}")
print(
    f"Jenkins token     : "
    f"{'LOADED' if JENKINS_TOKEN else 'NOT LOADED'}"
)
print(f"Job name          : {JOB_NAME}")
print(f"DevOps repository : {DEVOPS_REPO_URL}")
print(f"Git branch        : {GIT_BRANCH}")
print(f"Jenkinsfile       : {JENKINSFILE_PATH}")
print(
    f"Git credentials   : "
    f"{GIT_CREDENTIALS_ID if GIT_CREDENTIALS_ID else 'none'}"
)
print("=" * 70)
print()


if not JENKINS_TOKEN:
    print("ERROR: JENKINS_TOKEN was not found.")
    print()
    print(f"Expected .env file:")
    print(f"  {ENV_FILE}")
    print()
    print("Expected entry:")
    print()
    print("  JENKINS_TOKEN=your-jenkins-api-token")
    print()
    sys.exit(1)


if not DEVOPS_REPO_URL:
    print("ERROR: DEVOPS_REPO_URL is not configured.")
    print()
    print("Add your DevOps Git repository to .env:")
    print()
    print("DEVOPS_REPO_URL=https://github.com/YOUR-ORG/ecommerce-devops-infrastructure.git")
    print()
    sys.exit(1)


if "YOUR-ORG" in DEVOPS_REPO_URL:
    print("ERROR: DEVOPS_REPO_URL still contains YOUR-ORG.")
    print()
    print("Update .env with your actual Git repository URL.")
    print()
    sys.exit(1)


# ============================================================
# JENKINS SESSION
# ============================================================

session = requests.Session()

session.auth = (
    JENKINS_USER,
    JENKINS_TOKEN
)

session.headers.update({
    "Accept": "application/json"
})


# ============================================================
# CHECK JENKINS
# ============================================================

def check_jenkins():

    print("Checking Jenkins connectivity...")

    url = f"{JENKINS_URL}/api/json"

    try:
        response = session.get(
            url,
            timeout=15
        )
    except requests.exceptions.RequestException as exc:
        print()
        print("ERROR: Unable to connect to Jenkins.")
        print()
        print(f"URL: {JENKINS_URL}")
        print(f"Error: {exc}")
        print()
        sys.exit(1)

    if response.status_code != 200:

        print()
        print("ERROR: Jenkins API request failed.")
        print(f"HTTP status: {response.status_code}")
        print(response.text)
        print()

        sys.exit(1)

    print("Jenkins connectivity: OK")


# ============================================================
# GET CSRF CRUMB
# ============================================================

def get_crumb():

    print("Checking Jenkins CSRF protection...")

    url = f"{JENKINS_URL}/crumbIssuer/api/json"

    try:

        response = session.get(
            url,
            timeout=15
        )

    except requests.exceptions.RequestException as exc:

        print(
            f"WARNING: Could not contact Jenkins crumb endpoint: {exc}"
        )

        return

    if response.status_code == 200:

        try:

            data = response.json()

            field = data.get("crumbRequestField")
            crumb = data.get("crumb")

            if field and crumb:

                session.headers.update({
                    field: crumb
                })

                print("Jenkins CSRF crumb: loaded")
                return

        except Exception as exc:

            print(
                f"WARNING: Could not parse Jenkins crumb: {exc}"
            )

    elif response.status_code == 404:

        print(
            "Jenkins CSRF protection appears to be disabled."
        )

    else:

        print(
            f"WARNING: Jenkins crumb request returned "
            f"HTTP {response.status_code}"
        )


# ============================================================
# CHECK JOB
# ============================================================

def job_exists():

    url = (
        f"{JENKINS_URL}/job/"
        f"{quote(JOB_NAME, safe='')}"
        f"/api/json"
    )

    response = session.get(
        url,
        timeout=15
    )

    return response.status_code == 200


# ============================================================
# BUILD JENKINS PIPELINE XML
# ============================================================

def build_pipeline_xml():

    root = ET.Element(
        "flow-definition",
        {
            "plugin": "workflow-job"
        }
    )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description = ET.SubElement(
        root,
        "description"
    )

    description.text = (
        "E-Commerce DevOps Infrastructure CI Pipeline. "
        "Builds, tests, scans and packages the E-Commerce "
        "application using Maven, React, SonarQube, Semgrep, "
        "Trivy, Checkov, OWASP Dependency Check, Docker "
        "and AWS ECR."
    )

    # --------------------------------------------------------
    # Enabled
    # --------------------------------------------------------

    disabled = ET.SubElement(
        root,
        "disabled"
    )

    disabled.text = "false"

    # --------------------------------------------------------
    # Build retention
    # --------------------------------------------------------

    properties = ET.SubElement(
        root,
        "properties"
    )

    build_discarder = ET.SubElement(
        properties,
        "jenkins.model.BuildDiscarderProperty"
    )

    strategy = ET.SubElement(
        build_discarder,
        "strategy",
        {
            "class": "hudson.tasks.LogRotator"
        }
    )

    days_to_keep = ET.SubElement(
        strategy,
        "daysToKeepStr"
    )

    days_to_keep.text = "-1"

    num_to_keep = ET.SubElement(
        strategy,
        "numToKeepStr"
    )

    num_to_keep.text = "20"

    artifact_days = ET.SubElement(
        strategy,
        "artifactDaysToKeepStr"
    )

    artifact_days.text = "-1"

    artifact_num = ET.SubElement(
        strategy,
        "artifactNumToKeepStr"
    )

    artifact_num.text = "20"

    # --------------------------------------------------------
    # Pipeline definition
    # --------------------------------------------------------

    definition = ET.SubElement(
        root,
        "definition",
        {
            "class":
                "org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition",
            "plugin":
                "workflow-cps"
        }
    )

    # --------------------------------------------------------
    # Git SCM
    # --------------------------------------------------------

    scm = ET.SubElement(
        definition,
        "scm",
        {
            "class":
                "hudson.plugins.git.GitSCM",
            "plugin":
                "git"
        }
    )

    # --------------------------------------------------------
    # Git remote
    # --------------------------------------------------------

    user_remote_configs = ET.SubElement(
        scm,
        "userRemoteConfigs"
    )

    user_remote_config = ET.SubElement(
        user_remote_configs,
        "hudson.plugins.git.UserRemoteConfig"
    )

    url = ET.SubElement(
        user_remote_config,
        "url"
    )

    url.text = DEVOPS_REPO_URL

    if GIT_CREDENTIALS_ID:

        credentials = ET.SubElement(
            user_remote_config,
            "credentialsId"
        )

        credentials.text = GIT_CREDENTIALS_ID

    # --------------------------------------------------------
    # Git branch
    # --------------------------------------------------------

    branches = ET.SubElement(
        scm,
        "branches"
    )

    branch_spec = ET.SubElement(
        branches,
        "hudson.plugins.git.BranchSpec"
    )

    branch_name = ET.SubElement(
        branch_spec,
        "name"
    )

    branch_name.text = GIT_BRANCH

    # --------------------------------------------------------
    # Git extensions
    # --------------------------------------------------------

    ET.SubElement(
        scm,
        "extensions"
    )

    # --------------------------------------------------------
    # Lightweight checkout
    # --------------------------------------------------------

    lightweight = ET.SubElement(
        definition,
        "lightweight"
    )

    lightweight.text = "true"

    # --------------------------------------------------------
    # Jenkinsfile
    # --------------------------------------------------------

    script_path = ET.SubElement(
        definition,
        "scriptPath"
    )

    script_path.text = JENKINSFILE_PATH

    return ET.tostring(
        root,
        encoding="unicode"
    )


# ============================================================
# CREATE JOB
# ============================================================

def create_job():

    print()
    print(f"Creating Jenkins job: {JOB_NAME}")

    config_xml = build_pipeline_xml()

    url = (
        f"{JENKINS_URL}"
        f"/createItem?name={quote(JOB_NAME)}"
    )

    response = session.post(
        url,
        data=config_xml.encode("utf-8"),
        headers={
            "Content-Type": "application/xml"
        },
        timeout=30
    )

    if response.status_code not in (200, 201):

        print()
        print("ERROR: Failed to create Jenkins job.")
        print(f"HTTP status: {response.status_code}")
        print(response.text)
        print()

        sys.exit(1)

    print(
        f"Jenkins job created successfully: {JOB_NAME}"
    )


# ============================================================
# UPDATE JOB
# ============================================================

def update_job():

    print()
    print(f"Updating Jenkins job: {JOB_NAME}")

    config_xml = build_pipeline_xml()

    url = (
        f"{JENKINS_URL}/job/"
        f"{quote(JOB_NAME, safe='')}"
        f"/config.xml"
    )

    response = session.post(
        url,
        data=config_xml.encode("utf-8"),
        headers={
            "Content-Type": "application/xml"
        },
        timeout=30
    )

    if response.status_code != 200:

        print()
        print("ERROR: Failed to update Jenkins job.")
        print(f"HTTP status: {response.status_code}")
        print(response.text)
        print()

        sys.exit(1)

    print(
        f"Jenkins job updated successfully: {JOB_NAME}"
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary():

    print()
    print("=" * 70)
    print("JENKINS PIPELINE CONFIGURATION COMPLETE")
    print("=" * 70)

    print(f"Jenkins URL       : {JENKINS_URL}")
    print(f"Job name          : {JOB_NAME}")
    print("SCM               : Git")
    print(f"Repository        : {DEVOPS_REPO_URL}")
    print(f"Branch            : {GIT_BRANCH}")
    print(f"Jenkinsfile       : {JENKINSFILE_PATH}")
    print(
        f"Git credentials   : "
        f"{GIT_CREDENTIALS_ID or 'none'}"
    )

    print()
    print("Pipeline stages:")
    print()
    print("  1. Checkout")
    print("  2. Workspace Info")
    print("  3. Backend Unit Test")
    print("  4. Frontend Build")
    print("  5. Static Security - Semgrep")
    print("  6. Filesystem Security - Trivy")
    print("  7. IaC Security - Checkov")
    print("  8. Dependency Security - OWASP")
    print("  9. SonarQube")
    print(" 10. Docker Build")
    print(" 11. Container Security - Trivy")
    print(" 12. ECR Push")
    print(" 13. Container Sanity Test")

    print()
    print("Jenkins job URL:")
    print(
        f"{JENKINS_URL}/job/"
        f"{quote(JOB_NAME, safe='')}/"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    check_jenkins()

    get_crumb()

    if job_exists():

        print(
            f"Job already exists: {JOB_NAME}"
        )

        update_job()

    else:

        create_job()

    print_summary()

    print()
    print("Configuration completed.")
    print()
    print("The Jenkins job has NOT been automatically executed.")
    print("Review the Jenkins configuration before running Build #1.")
    print()


if __name__ == "__main__":
    main()

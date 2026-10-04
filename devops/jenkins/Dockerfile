FROM jenkins/jenkins:lts-jdk21

USER root

# ============================================================
# Base tools
# ============================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    jq \
    gnupg \
    python3 \
    python3-pip \
    python3-venv \
    unzip \
    zip \
    maven \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Docker CLI
# ============================================================
RUN curl -fsSL https://download.docker.com/linux/debian/gpg \
    | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Node.js 22
# ============================================================
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# AWS CLI
# ============================================================
RUN curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip \
    -o /tmp/awscliv2.zip \
    && unzip -q /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/aws /tmp/awscliv2.zip

# ============================================================
# Security tooling - Semgrep
# ============================================================
RUN python3 -m venv /opt/venvs/semgrep \
    && /opt/venvs/semgrep/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venvs/semgrep/bin/pip install --no-cache-dir semgrep

# ============================================================
# Security tooling - Checkov
# ============================================================
RUN python3 -m venv /opt/venvs/checkov \
    && /opt/venvs/checkov/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venvs/checkov/bin/pip install --no-cache-dir checkov

RUN ln -sf /opt/venvs/semgrep/bin/semgrep /usr/local/bin/semgrep \
    && ln -sf /opt/venvs/checkov/bin/checkov /usr/local/bin/checkov

# ============================================================
# Trivy
# ============================================================
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin

# ============================================================
# Jenkins Plugins
# ============================================================
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

RUN jenkins-plugin-cli \
    --plugin-file /usr/share/jenkins/ref/plugins.txt

# ============================================================
# Jenkins
# ============================================================
USER jenkins

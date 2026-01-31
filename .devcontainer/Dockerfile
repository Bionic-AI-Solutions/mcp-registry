# Use Python 3.11 base image and add Node.js
FROM python:3.11-slim-bullseye

# Install common development tools and dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    curl \
    git \
    vim \
    ca-certificates \
    gnupg \
    lsb-release \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x (pinned to specific version for reproducibility)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && node --version && npm --version

# Install Poetry for Python dependency management (pinned version)
RUN pip3 install --no-cache-dir "poetry>=1.7.0,<2.0.0" \
    && poetry --version

# Install kubectl (fixed command substitution)
RUN KUBECTL_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt) \
    && curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/kubectl \
    && kubectl version --client

# Install GitHub CLI (gh) - standalone binary for non-root install
RUN GH_VERSION=2.86.0 \
    && curl -sL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.tar.gz" -o /tmp/gh.tar.gz \
    && tar xzf /tmp/gh.tar.gz -C /tmp \
    && mv /tmp/gh_${GH_VERSION}_linux_amd64/bin/gh /usr/local/bin/gh \
    && chmod +x /usr/local/bin/gh \
    && rm -rf /tmp/gh.tar.gz /tmp/gh_${GH_VERSION}_linux_amd64 \
    && gh --version

# Install Docker CLI (will use host's Docker daemon via mount)
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install common Python packages (with version constraints for stability)
RUN pip3 install --no-cache-dir \
    "black>=23.0.0" \
    "flake8>=6.0.0" \
    "pylint>=3.0.0" \
    "pytest>=7.0.0" \
    "pytest-asyncio>=0.21.0" \
    "mypy>=1.0.0"

# Install common Node.js packages globally (with version constraints)
RUN npm install -g \
    "typescript@^5.0.0" \
    "ts-node@^10.9.0" \
    "eslint@^8.0.0" \
    "prettier@^3.0.0" \
    "nodemon@^3.0.0" \
    "@types/node@^20.0.0"

# Create vscode user (standard devcontainer user)
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid vscode --shell /bin/bash --create-home vscode \
    && mkdir -p /home/vscode/.local/bin \
    && chown -R vscode:vscode /home/vscode

# Set up workspace directory
WORKDIR /workspace

# Switch to vscode user
USER vscode

# Set up Python environment
ENV PATH="/home/vscode/.local/bin:${PATH}"

FROM ubuntu:22.04

WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clone Terraform at v1.10.0 release (pinned SHA)
RUN git init && \
    git remote add origin https://github.com/hashicorp/terraform.git && \
    git fetch --depth 1 origin 24236f4f0bd10ada71d70868abe15f9d88099747 && \
    git checkout FETCH_HEAD && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Create output directories
RUN mkdir -p /logs/agent /logs/verifier

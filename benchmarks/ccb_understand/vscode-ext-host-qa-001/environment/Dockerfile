FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install git and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates python3 && \
    rm -rf /var/lib/apt/lists/*

# Clone VS Code at pinned commit (v1.99.3)
RUN git init /workspace/vscode && \
    cd /workspace/vscode && \
    git remote add origin https://github.com/microsoft/vscode.git && \
    git fetch --depth 1 origin 17baf841131aa23349f217ca7c570c76ee87b957 && \
    git checkout FETCH_HEAD

WORKDIR /workspace/vscode

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install git and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates python3 && \
    rm -rf /var/lib/apt/lists/*

# Clone Cilium at pinned commit (v1.17.9)
RUN git init /workspace/cilium && \
    cd /workspace/cilium && \
    git remote add origin https://github.com/cilium/cilium.git && \
    git fetch --depth 1 origin a2f97aa8d2de4bb360bee1e295e20556ce4166ce && \
    git checkout FETCH_HEAD

WORKDIR /workspace/cilium

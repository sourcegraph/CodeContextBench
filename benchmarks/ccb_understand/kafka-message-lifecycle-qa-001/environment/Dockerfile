FROM ubuntu:22.04

# Install prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clone apache/kafka at pinned release tag 4.1.1
RUN git init /workspace && \
    cd /workspace && \
    git remote add origin https://github.com/apache/kafka.git && \
    git fetch --depth 1 origin 0753c489afad403fb6e78fda4c4a380e46f500c0 && \
    git checkout FETCH_HEAD

WORKDIR /workspace

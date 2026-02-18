FROM golang:1.23-bookworm

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Kubernetes at pinned commit
RUN git clone --filter=blob:none --no-checkout https://github.com/kubernetes/kubernetes.git . && \
    git checkout 8c9c67c000104450cfc5a5f48053a9a84b73cf93 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Remove existing test files from the target package
RUN rm -f staging/src/k8s.io/apimachinery/pkg/util/sets/*_test.go

# Download Go module dependencies for the sets package
RUN cd staging/src/k8s.io/apimachinery && go mod download

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

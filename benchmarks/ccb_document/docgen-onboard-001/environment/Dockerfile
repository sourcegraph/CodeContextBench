FROM golang:1.23-bookworm

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Istio at pinned commit
RUN git clone --filter=blob:none --no-checkout https://github.com/istio/istio.git . && \
    git checkout f8af3caeb1960d4cb1db5c4c0d4913c366625c71 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

FROM ubuntu:22.04

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Envoy at pinned commit
RUN git clone --filter=blob:none --no-checkout https://github.com/envoyproxy/envoy.git . && \
    git checkout 1d0ba73ad200d28e86c0c23f76c55320f82a8fba && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

FROM golang:1.23-bookworm

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    curl \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Clone Flipt at pinned commit
RUN git clone --filter=blob:none --no-checkout https://github.com/flipt-io/flipt.git . && \
    git checkout 3d5a345f94c2adc8a0eaa102c189c08ad4c0f8e8 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Download Go module dependencies
RUN go mod download

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

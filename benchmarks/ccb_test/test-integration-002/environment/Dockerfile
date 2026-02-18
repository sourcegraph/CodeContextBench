FROM golang:1.23-bookworm

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    curl \
    libtagc0-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Clone Navidrome at stable tag
RUN git clone --filter=blob:none --no-checkout https://github.com/navidrome/navidrome.git . && \
    git checkout v0.9.3 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Enable CGO for taglib and download dependencies
ENV CGO_ENABLED=1
RUN go mod download

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

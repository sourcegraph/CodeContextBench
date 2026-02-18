FROM golang:1.23-bookworm

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dual worktrees for version comparison
RUN git clone --filter=blob:none https://github.com/flipt-io/flipt.git /tmp/flipt && \
    cd /tmp/flipt && \
    git worktree add /workspace/v2.6.0 a92d41c003594d793999e57f7911e823a964ad7c && \
    git worktree add /workspace/v2.7.0 31ae0be1b561c4a52d3121667740502f0b613ce5

# Provide commit log between versions
RUN cd /tmp/flipt && \
    git log --oneline a92d41c003..31ae0be1b5 > /workspace/commit_log.txt

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone Terraform and create dual worktrees for version comparison
# v1.9.0 tag = 7637a9216e68f2812887eaf0722f9d3f9804c45e
# v1.10.0 tag = 24236f4f0bd10ada71d70868abe15f9d88099747
RUN git clone --filter=blob:none https://github.com/hashicorp/terraform.git /tmp/terraform && \
    cd /tmp/terraform && \
    git worktree add /workspace/v1.9.0 7637a9216e68f2812887eaf0722f9d3f9804c45e && \
    git worktree add /workspace/v1.10.0 24236f4f0bd10ada71d70868abe15f9d88099747

# Provide git log between versions for reference
RUN cd /tmp/terraform && \
    git log --oneline 7637a9216e..24236f4f0b > /workspace/commit_log.txt

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

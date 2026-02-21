FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openjdk-17-jdk \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Clone Kafka at the pinned version
RUN git clone --depth 1 --branch 3.9.0 https://github.com/apache/kafka.git /workspace

WORKDIR /workspace

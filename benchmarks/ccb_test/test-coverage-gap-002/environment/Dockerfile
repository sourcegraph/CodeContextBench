FROM eclipse-temurin:17-bookworm

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Kafka at pinned commit with sparse checkout
RUN git clone --filter=blob:none --no-checkout https://github.com/apache/kafka.git . && \
    git sparse-checkout init --cone && \
    git sparse-checkout set \
        clients/src/main/java/org/apache/kafka/clients/consumer \
        clients/src/test/java/org/apache/kafka/clients/consumer && \
    git checkout e678b4b && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

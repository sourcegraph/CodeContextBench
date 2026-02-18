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
    git sparse-checkout set clients/src/main/java/org/apache/kafka/common/record && \
    git checkout e678b4b && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Strip Javadoc comments from target files
RUN find clients/src/main/java/org/apache/kafka/common/record -name "*.java" \
    -exec python3 -c "\
import re, sys
for path in sys.argv[1:]:
    with open(path) as f:
        content = f.read()
    content = re.sub(r'/\*\*[\s\S]*?\*/', '/* [javadoc removed] */', content)
    with open(path, 'w') as f:
        f.write(content)
" {} +

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

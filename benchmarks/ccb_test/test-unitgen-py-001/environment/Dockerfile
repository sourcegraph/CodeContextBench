FROM python:3.12-bookworm

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Django at pinned commit
RUN git clone --filter=blob:none --no-checkout https://github.com/django/django.git . && \
    git checkout 674eda1c03a3187905f48afee0f15226aa62fdf3 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Install Django in development mode
RUN pip install -e .

# Remove existing serializer tests to force agent to write new ones
RUN rm -f tests/serializers/test_json.py 2>/dev/null || true

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

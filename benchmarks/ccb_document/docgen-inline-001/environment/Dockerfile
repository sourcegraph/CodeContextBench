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

# Strip docstrings from the target module so the agent must write them
RUN python3 -c "\
import re; \
path = 'django/middleware/security.py'; \
f = open(path); content = f.read(); f.close(); \
content = re.sub(r'(\"\"\"[\s\S]*?\"\"\")', '# [docstring removed]', content); \
f = open(path, 'w'); f.write(content); f.close(); \
"

RUN mkdir -p /app /logs/verifier

ENTRYPOINT []

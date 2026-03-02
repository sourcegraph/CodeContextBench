FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /ccb_crossrepo/src

RUN git clone --depth 1 https://github.com/sg-evals/django--674eda1c.git /ccb_crossrepo/src/django
RUN git clone --depth 1 https://github.com/sg-evals/flask--798e006f.git /ccb_crossrepo/src/flask
RUN git clone --depth 1 https://github.com/sg-evals/requests--421b8733.git /ccb_crossrepo/src/requests

RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true)

WORKDIR /workspace

RUN git init && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent" && \
    git config --global safe.directory '*'

RUN mkdir -p /logs/agent /logs/verifier && \
    chown -R claude:claude /workspace /logs /ccb_crossrepo

ENTRYPOINT []

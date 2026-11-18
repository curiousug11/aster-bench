# Science environment for ASTER-Bench. Not built or tested yet: the pilot ran on a plain host with
# env/setup_env.sh. Agent CLIs (claude, codex) and their credentials still need to be added per harness.
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends git curl unzip ca-certificates nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY setup_env.sh /opt/setup_env.sh
RUN bash /opt/setup_env.sh /opt/aster-bench-env

WORKDIR /bench

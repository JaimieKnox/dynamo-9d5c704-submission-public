FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

# Verifier deps, baked at build time (pinned) so nothing is installed at verify time.
RUN pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

COPY data/docs /app/docs
COPY data/rlaudit /app/rlaudit
COPY data/runs /app/runs

# Parent directory of every declared artifact must exist before the agent runs.
RUN mkdir -p /app/out

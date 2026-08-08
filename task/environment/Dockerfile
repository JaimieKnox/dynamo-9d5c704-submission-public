FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

COPY data/spec /app/spec
COPY data/cutreturn /app/cutreturn
COPY data/traces /app/traces
RUN mkdir -p /app/artifacts
# HARDNESS_BUST 2026-08-08 round5 raw-trunc open-frozen scale-pad

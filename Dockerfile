FROM python:3.13-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9.21 /uv /uvx /bin/
RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev git python3-dev

ENV PYTHONUNBUFFERED=1
ENV UV_MANAGED_PYTHON=1

WORKDIR /app
COPY . .
RUN uv sync
RUN uv run build.py


FROM debian:bookworm-slim
COPY --from=builder /app/dist/osbox /opt/osbox
ENV PATH="/opt/osbox:${PATH}"
ENTRYPOINT [ "osbox" ]
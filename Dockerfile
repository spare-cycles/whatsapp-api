FROM golang:1.25 AS wacli-builder

RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/steipete/wacli.git /build/wacli
WORKDIR /build/wacli
RUN go get go.mau.fi/whatsmeow@latest && go mod tidy
RUN CGO_ENABLED=1 go build -tags sqlite_fts5 -o /go/bin/wacli ./cmd/wacli

FROM python:3.13-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends libsqlite3-0 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.3.2 && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-interaction --no-ansi --no-root

COPY wacli_api/ wacli_api/

FROM base AS api

EXPOSE 9471
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
  CMD curl -fsS http://127.0.0.1:9471/health || exit 1
CMD ["uvicorn", "wacli_api.main:app", "--host", "0.0.0.0", "--port", "9471"]

FROM base AS sync

COPY --from=wacli-builder /go/bin/wacli /usr/local/bin/wacli
COPY sync_worker.py /app/sync_worker.py

FROM base AS mcp

COPY mcp_server.py /app/mcp_server.py
EXPOSE 9472
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9472/')" || exit 1
CMD ["python", "mcp_server.py"]

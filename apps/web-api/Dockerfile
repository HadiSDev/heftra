# Build from the repository root: docker build -f apps/web-api/Dockerfile .
FROM ghcr.io/astral-sh/uv:0.9-python3.12-bookworm-slim AS build

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
COPY apps/web-api/pyproject.toml apps/web-api/
COPY apps/ai-api/pyproject.toml apps/ai-api/
COPY apps/mock-erp/pyproject.toml apps/mock-erp/
RUN uv sync --frozen --package web-api --no-default-groups --no-dev --no-install-workspace

COPY apps/web-api/alembic.ini apps/web-api/
COPY apps/web-api/src apps/web-api/src
RUN uv sync --frozen --package web-api --no-default-groups --no-dev --no-editable

FROM python:3.12-slim-bookworm

RUN useradd --system --uid 10001 app
WORKDIR /app/apps/web-api
COPY --from=build --chown=app:app /app/.venv /app/.venv
COPY --from=build --chown=app:app /app/apps/web-api/alembic.ini /app/apps/web-api/alembic.ini
COPY --from=build --chown=app:app /app/apps/web-api/src /app/apps/web-api/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8100/api/v1/health')"

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn web_api.app:app --host 0.0.0.0 --port 8100 --proxy-headers --forwarded-allow-ips '*'"]

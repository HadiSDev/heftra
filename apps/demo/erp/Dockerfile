FROM python:3.12-slim-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --system --uid 10001 app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY demo_erp demo_erp

ENV PYTHONUNBUFFERED=1 \
    XDG_CACHE_HOME=/tmp/.cache
USER app
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/healthz')"
CMD ["uvicorn", "demo_erp.app:app", "--host", "0.0.0.0", "--port", "8001"]

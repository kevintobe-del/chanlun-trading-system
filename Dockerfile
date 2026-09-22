FROM node:22-bookworm-slim AS frontend

WORKDIR /app
COPY ui/package.json ui/package-lock.json ./ui/
RUN npm --prefix ui ci
COPY ui ./ui
COPY src ./src
RUN npm --prefix ui run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHANLUN_DATA_SOURCE_CONFIG=/config/data-sources.json \
    CHANLUN_WATCHLIST_CONFIG=/config/watchlists.json

RUN useradd --create-home --uid 10001 app
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY --from=frontend /app/src/chanlun_visual/static ./src/chanlun_visual/static

RUN python -m pip install --no-cache-dir ".[market]" && \
    mkdir -p /config && \
    chown -R app:app /config

USER app
EXPOSE 8791

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import json, urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:8791/api/health', timeout=3))['status'] == 'ok'"

CMD ["chanlun-visual", "--host", "0.0.0.0", "--port", "8791", "--no-browser"]

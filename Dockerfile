FROM ghcr.io/astral-sh/uv:0.12.13 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy UV_CACHE_DIR=/tmp/uv-cache MPLCONFIGDIR=/tmp/matplotlib EVIDENTLY_DISABLE_TELEMETRY=1
COPY pyproject.toml uv.lock ./
RUN uv sync --no-cache --locked --no-dev --no-install-project
COPY . .
RUN uv sync --no-cache --locked --no-dev --no-editable
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8001
CMD ["uvicorn", "churn_mlops.serve:app", "--host", "0.0.0.0", "--port", "8001"]

FROM python:3.11-slim AS builder

ENV VIRTUAL_ENV=/opt/venv \
    PIP_NO_CACHE_DIR=1

WORKDIR /opt/project

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime

LABEL maintainer="Gen-AI Team"
LABEL description="AI-powered travel booking system with LLM agents"
LABEL version="1.1.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}" \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

COPY src ./src
COPY scripts ./scripts
COPY requirements.txt ./requirements.txt

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

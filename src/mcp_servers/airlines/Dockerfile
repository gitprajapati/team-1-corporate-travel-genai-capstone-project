FROM python:3.11-slim AS builder

ENV VIRTUAL_ENV=/opt/venv \
    PIP_NO_CACHE_DIR=1

WORKDIR /opt/mcp

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

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}" \
    PORT=8001

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

COPY airlines/airline_booking_server.py ./airline_booking_server.py

EXPOSE 8001

CMD ["python", "airline_booking_server.py"]

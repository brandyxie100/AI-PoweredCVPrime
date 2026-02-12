# ─────────────────────────────────────────────────────────────
# Dockerfile — Analysis_CV_V2 (Multi-stage build)
# ─────────────────────────────────────────────────────────────
# Build:   docker build -t cv-analysis-api .
# Run:     docker run -p 8000:8000 --env-file .env cv-analysis-api
#
# Uses a multi-stage build:
#   Stage 1 (builder) — installs dependencies into a virtual env.
#   Stage 2 (runtime) — copies only the virtual env + app code,
#                        resulting in a smaller final image.
# ─────────────────────────────────────────────────────────────

# === Stage 1: Builder ===
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system deps needed to compile native extensions (faiss-cpu, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Create a virtual environment inside the builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies (cached layer — only re-runs if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# === Stage 2: Runtime ===
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code
COPY app/ ./app/

# Non-root user for security
RUN useradd --create-home appuser

# Create upload directory and give ownership to appuser
RUN mkdir -p /tmp/cv_uploads && chown appuser:appuser /tmp/cv_uploads

# Copy entrypoint script (fixes volume permissions at startup)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the API port
EXPOSE 8000

# Health-check (Docker will ping /health every 30s)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Entrypoint fixes volume permissions, then drops to appuser
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

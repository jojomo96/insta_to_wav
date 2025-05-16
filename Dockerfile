# ── Build stage ────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS build

# Install system packages that MoviePy (ffmpeg) needs
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first so Docker layer caching works when code changes
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Runtime stage (optional multi-stage) ───────────────────────────────────────
# If image size is critical you can switch to python:3.11-slim below and copy
# only /usr/bin/ffmpeg from the build stage.  For simplicity we reuse build.
# --------------------------------------------------------------------
# FROM python:3.11-slim
# COPY --from=build /usr/bin/ffmpeg /usr/bin/ffmpeg
# COPY --from=build /usr/local /usr/local
# WORKDIR /app
# COPY . .
# --------------------------------------------------------------------

COPY . .

# A non-root user is nice-to-have
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# ===== Build Stage =====
FROM python:3.13-slim AS build

# Install build deps for pyvips
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libvips-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

# Upgrade pip and install all Python deps (including pyvips)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend
COPY frontend/dist/ /app/frontend/dist

RUN chmod +x /app/backend/entrypoint.sh

# ===== Runtime Stage =====
FROM python:3.13-slim AS runtime

# Install runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libvips \
    tini \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed site-packages from build stage
COPY --from=build /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy app files
COPY --from=build /app/backend /app/backend
COPY --from=build /app/frontend/dist /app/frontend/dist

WORKDIR /app/backend

ENTRYPOINT ["/usr/bin/tini", "--", "/app/backend/entrypoint.sh"]
########################################
# Build stage: install deps with uv     #
########################################
FROM python:3.13-slim AS build

# Install build deps for pyvips and tools to install uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libvips-dev \
    libffi-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv (https://docs.astral.sh/uv/)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.profile
ENV PATH="/root/.local/bin:${PATH}"

# Copy only resolver inputs first for better Docker layer caching
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/uv.lock /app/backend/uv.lock

# Resolve and install project dependencies into a local virtualenv using the lockfile
WORKDIR /app/backend
RUN uv sync --frozen --no-dev

# Now copy the rest of the source tree
COPY backend/ /app/backend
COPY frontend/dist/ /app/frontend/dist

# Ensure scripts are executable
RUN chmod +x /app/backend/entrypoint.sh

########################################
# Runtime stage                        #
########################################
FROM python:3.13-slim AS runtime

# Install runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libvips \
    tini \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application and the prebuilt virtual environment from build stage
COPY --from=build /app/backend /app/backend
COPY --from=build /app/frontend/dist /app/frontend/dist

# Activate the venv for all subsequent commands/entrypoint
ENV VIRTUAL_ENV=/app/backend/.venv
ENV PATH="/app/backend/.venv/bin:${PATH}"

WORKDIR /app/backend

ENTRYPOINT ["/usr/bin/tini", "--", "/app/backend/entrypoint.sh"]
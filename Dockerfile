# ---- Build ----
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build tools (only needed for some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user -r requirements.txt

# Copy only the installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy source
COPY . .

# Heroku exposes PORT env var
EXPOSE $PORT

# Entrypoint
CMD ["python", "alpha.py"]

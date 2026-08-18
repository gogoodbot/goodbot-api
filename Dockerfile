FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies for production)
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY . .

EXPOSE 80

CMD ["uv", "run", "fastapi", "run", "/api/main.py", "--host", "0.0.0.0", "--port", "80", "--reload"]

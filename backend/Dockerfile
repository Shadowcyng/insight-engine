FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Install 'uv' directly from Astral's official binaries
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Copy your dependency files (assuming you use pyproject.toml and uv.lock)
COPY pyproject.toml uv.lock ./

# 3. Use uv to install dependencies into the system environment (--system)
RUN uv sync --frozen --no-cache --no-install-project

COPY . .

RUN uv sync --frozen --no-cache --no-install-project


CMD ["uv", "run","uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop", "--interface", "asgi3"]
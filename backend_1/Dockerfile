FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency definition files first to leverage Docker cache.
# This copies the most common files. Adjust this line if you use different file names.
COPY pyproject.toml* requirements.lock* requirements.txt* uv.lock* ./

# Install dependencies
# `uv sync --locked` will use pyproject.toml or requirements.lock
# This command will fail if the files copied above don't exist,
# so ensure your backend_1 directory contains them.
RUN uv sync --locked

# Copy the rest of the application source code
COPY . .

# Expose the port defined in your docker-compose.yml
EXPOSE 5001

# Run the application
# This assumes your entry point is app.py
CMD ["uv", "run", "app.py"]


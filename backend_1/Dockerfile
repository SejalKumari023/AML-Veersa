FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

# Use the app.py entry point which correctly uses the factory pattern
CMD ["python", "app.py"] 

# Use the official PostgreSQL image as the base
FROM postgres:latest

# Set environment variables for the PostgreSQL superuser password
# It is recommended to use Docker secrets or environment variables managed by orchestrators
# for production environments instead of hardcoding passwords in the Dockerfile.
ENV POSTGRES_PASSWORD=mysecretpassword

# Copy SQL initialization scripts into the entrypoint directory
# These scripts will be executed automatically when the container starts for the first time.
# The directory /docker-entrypoint-initdb.d is a special location recognized by the official Postgres image.
COPY init-scripts/ /docker-entrypoint-initdb.d/

# Expose the default PostgreSQL port (optional, but good practice for clarity)
EXPOSE 5432

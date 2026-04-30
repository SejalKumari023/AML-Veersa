FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

# Use the app.py entry point which correctly uses the factory pattern
CMD ["python", "app.py"] 
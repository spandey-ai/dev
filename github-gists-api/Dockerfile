# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . /app

EXPOSE 8080

# Use gunicorn with a small number of workers (adjust for your CPU)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "app:create_app()"]

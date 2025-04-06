# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies, including pkg-config and development libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir mysqlclient
RUN pip install --no-cache-dir django
RUN pip install gunicorn

# Copy the rest of the application
COPY BiotechBin ./BiotechBin
COPY django_website ./django_website
COPY manage.py .

# Expose port 8000
EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "django_website.wsgi:application"]
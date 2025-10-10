FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    inotify-tools

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Alembic 
RUN pip install alembic
COPY src/alembic.ini .
COPY src/alembic/ ./alembic/


# Copy application code
COPY start.sh /start.sh
COPY ./src ./src


# Create uploads directory
RUN mkdir -p /src/uploads

# Expose port
EXPOSE 8000

ENV PYTHONPATH=/app/src

# Run the application
CMD ["/start.sh"]
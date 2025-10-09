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
COPY alembic.ini .
COPY alembic/ ./alembic/


# Copy application code
COPY start.sh /start.sh
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Run the application
CMD ["/start.sh"]
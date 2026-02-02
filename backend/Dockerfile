FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    libtesseract-dev \
    poppler-utils \
    inotify-tools \
    && rm -rf /var/lib/apt/lists/*

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
COPY start.sh .
COPY ./src ./src

# Ensure script has Unix line endings and is executable in the image
RUN sed -i 's/\r$//' ./start.sh && chmod +x ./start.sh

# Create uploads directory in the copied source path
RUN mkdir -p /app/src/uploads

# Expose port
EXPOSE 8000

ENV PYTHONPATH=/app/src

# Run the application
CMD ["./start.sh"]
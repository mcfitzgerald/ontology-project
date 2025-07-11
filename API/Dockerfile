# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for owlready2)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache usage
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for ontology (will be mounted)
RUN mkdir -p /ontology

# Expose port
EXPOSE 8000

# Set environment variables
ENV ONTOLOGY_PATH=/ontology/mes_ontology_populated.owl
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
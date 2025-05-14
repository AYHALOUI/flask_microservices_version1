FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .

# Install system dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

COPY templates/ ./templates/

# Create directories
RUN mkdir -p /app/data

EXPOSE 5000

CMD ["python", "app.py"]
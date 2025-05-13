
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY app.py .

# Create directory for mapping files
RUN mkdir -p /app/mappings

# Copy mapping files
COPY mappings/contact_mapping.json /app/mappings/

# Expose the port
EXPOSE 5000

# Run the service
CMD ["python", "app.py"]
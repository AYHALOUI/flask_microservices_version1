FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY app.py .

# # Environment variables - to be overridden in deployment
# ENV OGGO_BASE_URL=https://api.oggo.com
# ENV OGGO_API_KEY=""
# ENV HUBSPOT_BASE_URL=https://api.hubspot.com
# ENV HUBSPOT_API_KEY=""
# ENV DEBUG=False

# Expose the port
EXPOSE 5000

# Run the service
CMD ["python", "app.py"]
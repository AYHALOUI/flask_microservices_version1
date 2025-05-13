# FROM node:16-alpine

# WORKDIR /app

# # Copy package.json first
# COPY package.json ./

# # Install dependencies
# RUN npm install --no-cache

# # Copy server code
# COPY server.js ./

# EXPOSE 3000

# CMD ["node", "server.js"]

FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY app.py .

# Expose the port
EXPOSE 5000

# Run the service
CMD ["python", "app.py"]
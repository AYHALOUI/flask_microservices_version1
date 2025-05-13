FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY app.py .

# create directories
RUN mkdir -p /app/data

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
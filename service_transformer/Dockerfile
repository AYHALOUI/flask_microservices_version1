
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /app/mappings

# Copy mapping files
COPY mappings/contact_mapping.json /app/mappings/

EXPOSE 5000

CMD ["python", "app.py"]
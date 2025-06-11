FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

COPY index.html .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Create directories
RUN mkdir -p /app/data

EXPOSE 5000

CMD ["python", "app.py"]
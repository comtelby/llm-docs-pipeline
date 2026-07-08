FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng \
    antiword catdoc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/input/uploads /app/input/configs /app/input/screenshots /app/input/samples /app/output /app/data /app/inventory /app/templates

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

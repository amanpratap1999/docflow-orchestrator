FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8003 8501

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port 8003 & streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0"]

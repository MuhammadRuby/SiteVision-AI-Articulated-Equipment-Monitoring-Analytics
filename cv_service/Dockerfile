FROM python:3.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt

RUN pip install --force-reinstall --no-cache-dir opencv-python-headless

COPY . .

CMD ["python", "app.py"]
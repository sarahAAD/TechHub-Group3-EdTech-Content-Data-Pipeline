FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت متصفح Chromium وكل مكتبات النظام اللي يحتاجها Playwright
RUN playwright install --with-deps chromium

COPY . .

CMD ["python", "run_ingestion.py"]

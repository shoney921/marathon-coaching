FROM python:3.9-slim

WORKDIR /app

# Python 패키지 경로 설정
ENV PYTHONPATH=/app:/app/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 
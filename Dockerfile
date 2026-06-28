FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-docker.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-docker.txt

COPY . .

EXPOSE 8000
EXPOSE 8101

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests

COPY path_overlay.py .

RUN chmod +x path_overlay.py
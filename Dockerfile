FROM python:3.11-slim

WORKDIR /app

# pehle requirements (layer caching ke liye)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
EXPOSE 7860

# Flask "app" object app.py me hai (main.py me nahi) -> app:app
# $PORT host (Railway/Render/Koyeb/HF) se aata hai; default 7860.
CMD ["sh", "-c", "gunicorn app:app -b 0.0.0.0:${PORT:-7860} --workers 2 --threads 4 --timeout 120"]

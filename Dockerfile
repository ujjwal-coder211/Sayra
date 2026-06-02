FROM python:3.9-slim

# OpenCV / matplotlib ke liye system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# pehle requirements (layer caching ke liye)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
EXPOSE 7860

# Flask "app" object app.py me hai (main.py me nahi) -> app:app
# TensorFlow heavy hai: 1 worker + bada timeout. $PORT Railway/Render se aata hai.
CMD ["sh", "-c", "gunicorn app:app -b 0.0.0.0:${PORT:-7860} --workers 1 --threads 4 --timeout 180"]

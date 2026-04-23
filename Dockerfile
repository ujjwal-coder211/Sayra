FROM python:3.9-slim
# ज़रूरी सिस्टम फाइल्स
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
# सारी लाइब्रेरीज़ इंस्टॉल करना
RUN pip install --no-cache-dir -r requirements.txt
# हगिंग फेस के लिए पोर्ट 7860
ENV FLASK_APP=main.py
EXPOSE 7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "main:app"]
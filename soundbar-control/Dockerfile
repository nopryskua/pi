FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV SOUNDBAR_IP=192.168.1.113
ENV SOUNDBAR_PORT=9741

EXPOSE 5050

CMD ["python", "app.py"]


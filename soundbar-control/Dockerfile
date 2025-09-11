FROM python:3.11-slim

WORKDIR /app

# Install git and other necessary packages
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV SOUNDBAR_IP=192.168.1.113

EXPOSE 5050

CMD ["python", "app.py"]


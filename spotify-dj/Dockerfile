FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install requests flask openai pydantic pygame

COPY app.py .

CMD ["python", "app.py"]

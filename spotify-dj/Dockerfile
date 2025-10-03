FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install requests flask openai pydantic pygame

ARG UID=1000
ARG GID=1000
ARG USER=appuser

RUN groupadd -g $GID $USER && \
    useradd -m -u $UID -g $GID -s /bin/bash $USER

USER $USER
WORKDIR /home/$USER

COPY app.py .

CMD ["python", "app.py"]

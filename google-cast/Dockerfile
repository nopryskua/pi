# Use slim Python base
FROM python:3.12-slim

# Install dependencies
RUN pip install --no-cache-dir pychromecast

# Copy your wake script into container
WORKDIR /app
COPY wake_cast.py .

# Default command (run the script)
CMD ["python", "wake_cast.py"]


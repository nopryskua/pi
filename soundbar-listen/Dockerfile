FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir flask pycryptodome

# Copy the listener/server
COPY server.py .

# Expose port (default 5050)
EXPOSE 5050

# Start the listener and API server
CMD ["python", "server.py"]

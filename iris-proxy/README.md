# Iris Proxy

A simple HTTP proxy service that wakes up the soundbar and redirects to Iris.

## Functionality

- **Port**: Listens on port 6681
- **Main behavior**: When you visit `http://localhost:6681`, it:
  1. Calls `http://pi:5050/setup` to wake up the soundbar
  2. Redirects you to `http://pi:6680/iris`

## Endpoints

- `GET /` - Main endpoint: wakes up soundbar then redirects to iris
- `GET /health` - Health check endpoint

## Usage

Simply open `http://localhost:6681` in your browser. The proxy will:
1. Automatically wake up your soundbar
2. Redirect you to the Iris web interface

## Building and Running

### Docker

```bash
# Build the image
docker build -t iris-proxy .

# Run the container
docker run -d --name iris-proxy --network host --restart unless-stopped iris-proxy

# Firewall
sudo ufw allow from 192.168.1.0/24 to any port 6681 proto tcp
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## Environment Variables

- `PORT` - Port to listen on (default: 6681)
- `HOST` - Host to bind to (default: 0.0.0.0)

## Health Check

The service includes a health check endpoint at `/health` and Docker health check configuration.

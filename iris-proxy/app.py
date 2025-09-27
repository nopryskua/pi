#!/usr/bin/env python3
import os
import requests
from flask import Flask, request, redirect, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
SETUP_URL = "http://localhost:5050/setup"
IRIS_URL = "http://pi:6680/iris"

@app.route('/', methods=['GET'])
def root():
    """
    Main endpoint: wake up soundbar then redirect to iris
    """
    try:
        logger.info("Received request to root endpoint")
        
        # First, wake up the soundbar by calling the setup endpoint
        logger.info(f"Waking up soundbar: calling {SETUP_URL}")
        try:
            setup_response = requests.post(SETUP_URL, timeout=10)
            logger.info(f"Setup response status: {setup_response.status_code}")
        except requests.exceptions.Timeout:
            logger.warning("Timeout while waking up soundbar, continuing anyway")
        except requests.exceptions.ConnectionError:
            logger.warning("Could not connect to soundbar setup, continuing anyway")
        except Exception as e:
            logger.warning(f"Error waking up soundbar: {str(e)}, continuing anyway")
        
        # Then redirect to iris
        logger.info(f"Redirecting to {IRIS_URL}")
        return redirect(IRIS_URL, code=302)
        
    except Exception as e:
        logger.error(f"Error in root endpoint: {str(e)}")
        return jsonify({"error": f"Proxy error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({"status": "healthy", "service": "iris-proxy"}), 200

if __name__ == "__main__":
    port = int(os.getenv('PORT', 6681))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting Iris Proxy Server on {host}:{port}")
    logger.info(f"Setup endpoint: {SETUP_URL}")
    logger.info(f"Iris endpoint: {IRIS_URL}")
    
    app.run(host=host, port=port, debug=False)

import os
import sys
import requests
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPES = "user-modify-playback-state user-read-playback-state user-read-currently-playing"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if "code" not in params:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code")
            return
        code = params["code"][0]

        # Exchange code for tokens
        resp = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        resp.raise_for_status()
        tokens = resp.json()

        refresh_token = tokens.get("refresh_token")
        access_token = tokens.get("access_token")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"You can close this window now.\n")

        print("\n--- SUCCESS ---")
        print("Refresh token:", refresh_token)
        print("Access token (short-lived):", access_token)
        sys.exit(0)

def run_server():
    url = (
        f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&scope={urllib.parse.quote(SCOPES)}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    )
    print("Open this URL in your browser:\n", url)
    httpd = HTTPServer(("0.0.0.0", 8888), Handler)
    httpd.serve_forever()

if __name__ == "__main__":
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars.")
        sys.exit(1)
    run_server()


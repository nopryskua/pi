#!/usr/bin/env python3
import os
import requests
from flask import Flask, request, render_template_string, redirect, url_for, flash

API_URL = "http://127.0.0.1:9117/api/v2.0/indexers/all/results"
API_KEY = os.getenv("JACKETT_API_KEY")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jackett Torrent Search</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 1.1rem;
        }
        
        .search-section {
            padding: 30px;
            background: #f8f9fa;
        }
        
        .search-form {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr auto;
            gap: 15px;
            align-items: end;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            font-weight: 600;
            margin-bottom: 5px;
            color: #2c3e50;
            font-size: 0.9rem;
        }
        
        .form-group input {
            padding: 12px 15px;
            border: 2px solid #e1e8ed;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .search-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            height: fit-content;
        }
        
        .search-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .search-btn:active {
            transform: translateY(0);
        }
        
        
        .results-section {
            padding: 30px;
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e1e8ed;
        }
        
        .results-count {
            font-size: 1.1rem;
            color: #2c3e50;
            font-weight: 600;
        }
        
        .torrent-item {
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .torrent-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        
        .torrent-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
            line-height: 1.4;
        }
        
        .torrent-meta {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 5px;
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .meta-item strong {
            color: #2c3e50;
        }
        
        .seeders {
            color: #28a745 !important;
        }
        
        .peers {
            color: #17a2b8 !important;
        }
        
        .size {
            color: #fd7e14 !important;
        }
        
        .add-btn {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .add-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3);
        }
        
        .add-btn:active {
            transform: translateY(0);
        }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-size: 1.1rem;
        }
        
        .alert {
            padding: 15px 20px;
            margin: 20px 30px;
            border-radius: 8px;
            font-weight: 500;
        }
        
        .alert-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        @media (max-width: 768px) {
            .search-form {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            
            .torrent-meta {
                flex-direction: column;
                gap: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .container {
                margin: 10px;
                border-radius: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Jackett Torrent Search</h1>
            <p>Search and add torrents directly to Transmission</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert alert-{{ category if category != 'message' else 'info' }}">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        
        <div class="search-section">
            <form method="post" class="search-form" id="searchForm">
                <div class="form-group">
                    <label for="query">Search Query</label>
                    <input name="query" id="query" placeholder="Enter search terms..." required
                           value="{{ request.form.get('query', '') }}" autocomplete="off">
                </div>
                <div class="form-group">
                    <label for="min_size">Min Size (GB)</label>
                    <input name="min_size" id="min_size" placeholder="0.1" type="number" step="0.1"
                           value="{{ request.form.get('min_size', '') }}">
                </div>
                <div class="form-group">
                    <label for="max_size">Max Size (GB)</label>
                    <input name="max_size" id="max_size" placeholder="10.0" type="number" step="0.1"
                           value="{{ request.form.get('max_size', '') }}">
                </div>
                <div class="form-group">
                    <label for="min_seeders">Min Seeders</label>
                    <input name="min_seeders" id="min_seeders" placeholder="1" type="number"
                           value="{{ request.form.get('min_seeders', '') }}">
                </div>
                <button type="submit" class="search-btn">Search</button>
            </form>
        </div>
        
        {% if results is not none %}
          <div class="results-section">
            {% if results %}
              <div class="results-header">
                <div class="results-count">
                  Found {{ results|length }} torrent{{ 's' if results|length != 1 else '' }}
                </div>
              </div>
              
              {% for e in results %}
                <div class="torrent-item">
                  <div class="torrent-title">{{e.Title}}</div>
                  <div class="torrent-meta">
                    <div class="meta-item">
                      <span>📦</span>
                      <span class="size"><strong>{{e.SizeGB}} GB</strong></span>
                    </div>
                    <div class="meta-item">
                      <span>⬆️</span>
                      <span class="seeders"><strong>{{e.Seeders}}</strong> seeders</span>
                    </div>
                    <div class="meta-item">
                      <span>👥</span>
                      <span class="peers"><strong>{{e.Peers}}</strong> peers</span>
                    </div>
                  </div>
                  <form method="post" action="/add_magnet" style="display: inline;">
                    <input type="hidden" name="magnet" value="{{e.Magnet}}">
                    <input type="hidden" name="title" value="{{e.Title}}">
                    <button type="submit" class="add-btn">
                      ➕ Add to Transmission
                    </button>
                  </form>
                </div>
              {% endfor %}
            {% else %}
              <div class="no-results">
                <h3>No results found</h3>
                <p>Try adjusting your search criteria or filters</p>
              </div>
            {% endif %}
          </div>
        {% endif %}
    </div>
    
    <script>
        // Add keyboard shortcut (Ctrl+Enter to search)
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                document.getElementById('searchForm').submit();
            }
        });
        
        // Auto-focus search input
        document.getElementById('query').focus();
    </script>
</body>
</html>
"""

def human_size(b): return round(b / (1024 ** 3), 2)

def add_magnet_to_transmission(magnet_url):
    """Add a magnet URL to Transmission daemon via RPC API"""
    try:
        # Transmission RPC configuration (using localhost since Docker runs with --network host)
        transmission_host = os.getenv('TRANSMISSION_HOST', '127.0.0.1')
        transmission_port = os.getenv('TRANSMISSION_PORT', '9091')
        transmission_url = f"http://{transmission_host}:{transmission_port}/transmission/rpc"
        
        # Get session ID first
        session_response = requests.get(transmission_url, timeout=10)
        session_id = session_response.headers.get('X-Transmission-Session-Id')
        
        if not session_id:
            return False, "Could not get Transmission session ID"
        
        # Add torrent via RPC
        rpc_data = {
            "method": "torrent-add",
            "arguments": {
                "filename": magnet_url
            }
        }
        
        headers = {
            'X-Transmission-Session-Id': session_id,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            transmission_url, 
            json=rpc_data, 
            headers=headers, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('result') == 'success':
                return True, "Torrent added successfully!"
            else:
                return False, f"Transmission error: {result.get('result', 'Unknown error')}"
        else:
            return False, f"HTTP error: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout while connecting to Transmission"
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to Transmission daemon"
    except Exception as e:
        return False, f"Error: {str(e)}"

def resolve_magnet(entry):
    if entry.get("MagnetUri"): 
        return entry["MagnetUri"]
    if entry.get("Guid", "").startswith("magnet:?"): 
        return entry["Guid"]
    if entry.get("Link"):
        try:
            r = requests.get(entry["Link"], allow_redirects=False, timeout=10)
            if r.headers.get("Location", "").startswith("magnet:?"):
                return r.headers["Location"]
        except Exception:
            return None
    return None

def search(query):
    if not API_KEY:
        raise ValueError("JACKETT_API_KEY environment variable is not set")
    
    try:
        r = requests.get(API_URL, params={"apikey": API_KEY, "Query": query}, timeout=120)
        r.raise_for_status()
        return r.json().get("Results", [])
    except requests.exceptions.Timeout:
        raise Exception("Jackett API request timed out")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to Jackett API")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Jackett API error: {e}")
    except Exception as e:
        raise Exception(f"Search error: {str(e)}")

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        
        # Validate query
        if not query:
            flash("Please enter a search query", "error")
            return render_template_string(TEMPLATE, results=results)
        
        min_size = request.form.get("min_size", type=float)
        max_size = request.form.get("max_size", type=float)
        min_seeders = request.form.get("min_seeders", type=int)

        try:
            clauses = query.lower().split()
            raw_results = search(query)
            results = []

            for entry in raw_results:
                size_gb = human_size(entry.get("Size", 0))
                if min_size and size_gb < min_size: continue
                if max_size and size_gb > max_size: continue
                if min_seeders and entry.get("Seeders", 0) < min_seeders: continue
                title = entry.get("Title", "").lower()
                if not all(c in title for c in clauses): continue
                magnet = resolve_magnet(entry)
                if not magnet: continue
                results.append({
                    "Title": entry.get("Title", "N/A"),
                    "SizeGB": size_gb,
                    "Seeders": entry.get("Seeders", 0),
                    "Peers": entry.get("Peers", 0),
                    "Magnet": magnet
                })
            
            # Sort results by seed count in descending order (highest first)
            results.sort(key=lambda x: x["Seeders"], reverse=True)
            
        except Exception as e:
            flash(f"Search failed: {str(e)}", "error")
            return render_template_string(TEMPLATE, results=results)

    return render_template_string(TEMPLATE, results=results)

@app.route("/add_magnet", methods=["POST"])
def add_magnet():
    magnet_url = request.form.get("magnet", "").strip()
    title = request.form.get("title", "Unknown").strip()
    
    if not magnet_url:
        flash("No magnet URL provided", "error")
        return redirect(url_for("index"))
    
    if not magnet_url.startswith("magnet:?"):
        flash("Invalid magnet URL format", "error")
        return redirect(url_for("index"))
    
    try:
        success, message = add_magnet_to_transmission(magnet_url)
        
        if success:
            flash(f"Successfully added '{title}' to Transmission!", "success")
        else:
            flash(f"Failed to add '{title}': {message}", "error")
    except Exception as e:
        flash(f"Error adding torrent: {str(e)}", "error")
    
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Check if API key is configured
    if not API_KEY:
        print("ERROR: JACKETT_API_KEY environment variable is not set!")
        print("Please set it with: export JACKETT_API_KEY='your-api-key-here'")
        exit(1)
    
    print("Starting Jackett Search Server...")
    print(f"API Key configured: {'*' * (len(API_KEY) - 4) + API_KEY[-4:] if len(API_KEY) > 4 else '***'}")
    print("Server will be available at: http://0.0.0.0:5000")
    
    app.run(host="0.0.0.0", port=5000)


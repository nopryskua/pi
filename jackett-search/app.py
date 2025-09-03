#!/usr/bin/env python3
import os
import requests
from flask import Flask, request, render_template_string

API_URL = "http://127.0.0.1:9117/api/v2.0/indexers/all/results"
API_KEY = os.getenv("JACKETT_API_KEY")

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<title>Jackett Search</title>
<h1>Jackett Torrent Search</h1>
<form method="post">
  <input name="query" placeholder="Search query" required style="width:200px">
  <input name="min_size" placeholder="Min GB" type="number" step="0.1" style="width:80px">
  <input name="max_size" placeholder="Max GB" type="number" step="0.1" style="width:80px">
  <input name="min_seeders" placeholder="Min seeders" type="number" style="width:80px">
  <button type="submit">Search</button>
</form>

{% if results is not none %}
  <hr>
  {% if results %}
    {% for e in results %}
      <div style="margin-bottom:12px;">
        <strong>{{e.Title}}</strong><br>
        Size: {{e.SizeGB}} GB | Seeders: {{e.Seeders}} | Peers: {{e.Peers}}<br>
        <a href="{{e.Magnet}}">Magnet</a>
      </div>
    {% endfor %}
  {% else %}
    <p>No results matched filters.</p>
  {% endif %}
{% endif %}
"""

def human_size(b): return round(b / (1024 ** 3), 2)

def resolve_magnet(entry):
    if entry.get("MagnetUri"): return entry["MagnetUri"]
    if entry.get("Guid", "").startswith("magnet:?"): return entry["Guid"]
    if entry.get("Link"):
        try:
            r = requests.get(entry["Link"], allow_redirects=False, timeout=10)
            if r.headers.get("Location", "").startswith("magnet:?"):
                return r.headers["Location"]
        except: return None
    return None

def search(query):
    r = requests.get(API_URL, params={"apikey": API_KEY, "Query": query}, timeout=120)
    r.raise_for_status()
    return r.json().get("Results", [])

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        query = request.form.get("query", "")
        min_size = request.form.get("min_size", type=float)
        max_size = request.form.get("max_size", type=float)
        min_seeders = request.form.get("min_seeders", type=int)

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

    return render_template_string(TEMPLATE, results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


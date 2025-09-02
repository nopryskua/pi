#!/usr/bin/env python3
import argparse
import requests
import sys
import os

API_URL = "http://localhost:9117/api/v2.0/indexers/all/results"
API_KEY = os.getenv("JACKETT_API_KEY")


def resolve_magnet(entry):
    """
    Extract magnet link from an entry:
    1. MagnetUri field
    2. Guid if it's a magnet
    3. Link -> request -> Location header
    """
    if entry.get("MagnetUri"):
        return entry["MagnetUri"]

    if entry.get("Guid", "").startswith("magnet:?"):
        return entry["Guid"]

    if entry.get("Link"):
        try:
            r = requests.get(entry["Link"], allow_redirects=False, timeout=10)
            if "Location" in r.headers and r.headers["Location"].startswith("magnet:?"):
                return r.headers["Location"]
        except Exception as e:
            sys.stderr.write(f"Error resolving Link for {entry.get('Title')}: {e}\n")
    return None


def human_size(bytes_val):
    gb = bytes_val / (1024 ** 3)
    return f"{gb:.2f} GB"


def search(query):
    params = {
        "apikey": API_KEY,
        "Query": query,
    }
    r = requests.get(API_URL, params=params, timeout=120)
    r.raise_for_status()
    return r.json().get("Results", [])


def passes_filters(entry, query_clauses, min_size_gb, max_size_gb, min_seeders):
    # Size filter
    size_gb = entry.get("Size", 0) / (1024 ** 3)
    if min_size_gb is not None and size_gb < min_size_gb:
        return False
    if max_size_gb is not None and size_gb > max_size_gb:
        return False

    # Seeder filter
    seeders = entry.get("Seeders", 0)
    if min_seeders is not None and seeders < min_seeders:
        return False

    # Query clause filter
    title = entry.get("Title", "").lower()
    for clause in query_clauses:
        if clause not in title:
            return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Jackett Torrent Search Tool")
    parser.add_argument("--query", required=True, help="Search query string")
    parser.add_argument("--min-size-gb", type=float, help="Minimum size in GB")
    parser.add_argument("--max-size-gb", type=float, help="Maximum size in GB")
    parser.add_argument("--min-seeders", type=int, help="Minimum number of seeders")
    args = parser.parse_args()

    query_clauses = args.query.lower().split()
    results = search(args.query)

    if not results:
        print("No results found.")
        return

    shown = False
    for entry in results:
        if not passes_filters(entry, query_clauses, args.min_size_gb, args.max_size_gb, args.min_seeders):
            continue

        magnet = resolve_magnet(entry)
        if not magnet:
            continue

        title = entry.get("Title", "N/A")
        size = human_size(entry.get("Size", 0))
        peers = entry.get("Peers", 0)
        seeders = entry.get("Seeders", 0)

        print(f"{title}\n  Size: {size} | Seeders: {seeders} | Peers: {peers}")
        print(f"  Magnet: {magnet}\n")
        shown = True

    if not shown:
        print("No results matched the filters.")


if __name__ == "__main__":
    main()


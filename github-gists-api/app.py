from __future__ import annotations

import os
import re
import time
import logging
from typing import Any, Dict, Optional, Tuple, List
from urllib.parse import urlencode

import requests
from flask import Flask, jsonify, request, Response, send_from_directory

USERNAME_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 6  # seconds
MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 30
DEFAULT_PAGE = 1

# Simple in-memory cache: key -> (expires_at, data)
_CACHE: Dict[Tuple[str, int, int], Tuple[float, Dict[str, Any]]] = {}

def get_cache_ttl() -> int:
    try:
        return int(os.getenv("GIST_CACHE_TTL", "60"))
    except ValueError:
        return 60

def _cache_get(key: Tuple[str, int, int]) -> Optional[Dict[str, Any]]:
    now = time.time()
    slot = _CACHE.get(key)
    if not slot:
        return None
    expires_at, data = slot
    if now >= expires_at:
        # expired
        _CACHE.pop(key, None)
        return None
    return data

def _cache_set(key: Tuple[str, int, int], data: Dict[str, Any]) -> None:
    ttl = max(0, get_cache_ttl())
    _CACHE[key] = (time.time() + ttl, data)

def _github_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "gists-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def _parse_link_header(link_header: Optional[str]) -> Dict[str, Optional[int]]:
    """
    Parse GitHub-style Link header and extract page numbers for rels.
    Returns dict with keys: first, prev, next, last -> Optional[int]
    """
    rels: Dict[str, Optional[int]] = {"first": None, "prev": None, "next": None, "last": None}
    if not link_header:
        return rels
    parts = [p.strip() for p in link_header.split(",")]
    for part in parts:
        # Example: <https://api.github.com/users/octocat/gists?page=2?per_page=30>; rel="next"
        m = re.match(r'<[^>]*[?&]page=(\d+)[^>]*>\s*;\s*rel="(\w+)"', part)
        if m:
            page = int(m.group(1))
            rel = m.group(2)
            if rel in rels:
                rels[rel] = page
    return rels

def fetch_gists(username: str, page: int, per_page: int) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
    """
    Calls GitHub API for user's public gists.
    Returns (status_code, payload_json (if any), response_headers)
    """
    params = {"page": page, "per_page": per_page}
    url = f"{GITHUB_API}/users/{username}/gists"
    try:
        resp = requests.get(url, headers=_github_headers(), params=params, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as e:
        # Upstream is unreachable or timed out
        return 502, {"error": "Upstream GitHub API unreachable", "details": str(e)}, {}

    # Map some common status codes directly
    if resp.status_code == 404:
        return 404, {"error": "User not found"}, {}
    if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
        return 429, {"error": "GitHub rate limit exceeded. Try again later."}, {}

    if not resp.ok:
        # Pass-through basic error details
        try:
            payload = resp.json()
        except Exception:
            payload = {"error": "Upstream error", "status": resp.status_code}
        return 502, payload, {}

    try:
        data = resp.json()
    except ValueError:
        return 502, {"error": "Invalid JSON from GitHub"}, {}

    # Normalize output: pick a few useful fields
    gists: List[Dict[str, Any]] = []
    for g in data:
        files = list(g.get("files", {}).keys())
        gists.append({
            "id": g.get("id"),
            "description": g.get("description"),
            "html_url": g.get("html_url"),
            "files": files,
            "public": g.get("public"),
            "created_at": g.get("created_at"),
            "updated_at": g.get("updated_at"),
        })

    # Pagination hints from Link header
    rels = _parse_link_header(resp.headers.get("Link"))

    payload = {
        "user": username,
        "page": page,
        "per_page": per_page,
        "count": len(gists),
        "gists": gists,
        "pagination": rels,
    }
    # Return 200 and include select headers if helpful
    headers = {}
    # echo useful rate limit headers if present
    for k in ("X-RateLimitRemaining", "X-RateLimit-Reset", "X-RateLimit-Limit"):
        if k in resp.headers:
            headers[k] = resp.headers[k]
    return 200, payload, headers

def create_app() -> Flask:
    app = Flask(__name__)

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("gists-api")
    
    @app.get("/healthz")
    def health() -> Response:
        return jsonify({"status": "ok"})

    @app.get("/")
    def root() -> Response:
        return jsonify({"message": "Use /<github-username> to fetch public gists", "example": "/octocat"})

    @app.get("/<string:username>")
    def list_gists(username: str) -> Response:
        if not USERNAME_RE.match(username):
            return jsonify({"error": "Invalid username format"}), 400

        # Validate and coerce pagination
        def to_int(name: str, default: int) -> int:
            raw = request.args.get(name, default)
            try:
                return int(raw)
            except (TypeError, ValueError):
                raise ValueError(f"Query parameter '{name}' must be an integer")

        try:
            page = to_int("page", DEFAULT_PAGE)
            per_page = to_int("per_page", DEFAULT_PER_PAGE)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        if page < 1:
            return jsonify({"error": "page must be >= 1"}), 400
        if per_page < 1 or per_page > MAX_PER_PAGE:
            return jsonify({"error": f"per_page must be between 1 and {MAX_PER_PAGE}"}), 400

        cache_key = (username, page, per_page)
        cached = _cache_get(cache_key)
        if cached is not None:
            # Indicate cache hit in a header
            resp = jsonify(cached)
            resp.headers["X-Cache"] = "HIT"
            return resp, 200

        status, payload, headers = fetch_gists(username, page, per_page)
        if status == 200:
            _cache_set(cache_key, payload)
        resp = jsonify(payload)
        for k, v in headers.items():
            resp.headers[k] = v
        if status == 200:
            resp.headers["X-Cache"] = "MISS"
        return resp, status

    return app

if __name__ == "__main__":
    # Dev server
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=False)

import json
import os
import re
import pytest
from flask import Flask
import responses

from app import create_app

@pytest.fixture()
def client():
    app: Flask = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client

def github_url(username="don7781", page=1, per_page=30):
    return f"https://api.github.com/users/{username}/gists?page={page}&per_page={per_page}"

@responses.activate
def test_list_gists_ok(client):
    sample = [
        {
            "id": "aa5a315d61ae9438b18d",
            "description": "Hello world gist",
            "html_url": "https://gist.github.com/aa5a315d61ae9438b18d",
            "files": {"hello_world.py": {"filename": "hello_world.py"}},
            "public": True,
            "created_at": "2021-01-01T00:00:00Z",
            "updated_at": "2021-01-01T00:00:00Z",
        }
    ]

    responses.add(
        responses.GET,
        re.compile(r"https://api\.github\.com/users/octocat/gists\?page=1&per_page=30"),
        json=sample,
        status=200,
        headers={"Link": '<https://api.github.com/users/octocat/gists?page=2&per_page=30>; rel="next"'},
    )

    resp = client.get("/octocat")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["user"] == "octocat"
    assert body["count"] == 1
    assert body["gists"][0]["id"] == "aa5a315d61ae9438b18d"
    # Pagination parsed from Link header
    assert body["pagination"]["next"] == 2

@responses.activate
def test_user_not_found_maps_to_404(client):
    responses.add(
        responses.GET,
        re.compile(r"https://api\.github\.com/users/doesnotexist/gists\?page=1&per_page=30"),
        status=404,
        json={"message": "Not Found"},
    )
    resp = client.get("/doesnotexist")
    assert resp.status_code == 404
    body = resp.get_json()
    assert "error" in body

def test_invalid_query_params(client):
    r = client.get("/octocat?per_page=0")
    assert r.status_code == 400
    assert "per_page" in r.get_json()["error"]

    r = client.get("/octocat?page=0")
    assert r.status_code == 400
    assert "page" in r.get_json()["error"]

def test_invalid_username(client):
    r = client.get("/bad/user")  # slash not allowed, route will treat 'bad' as username
    assert r.status_code == 404  # '/bad' exists; ensure invalid username is rejected on pattern
    # Specifically check invalid chars:
    r = client.get("/bad_user!")  # invalid characters '!' and '_' based on our regex
    assert r.status_code == 400
    assert "Invalid username" in r.get_json()["error"]

@responses.activate
def test_cache_header_present(client):
    sample = []
    responses.add(
        responses.GET,
        re.compile(r"https://api\.github\.com/users/octocat/gists\?page=1&per_page=30"),
        json=sample,
        status=200,
    )
    r1 = client.get("/octocat")
    assert r1.status_code == 200
    assert r1.headers.get("X-Cache") in ["MISS", "HIT"]

    # Second call should come from cache (no new responses added)
    r2 = client.get("/octocat")
    assert r2.status_code == 200
    assert r2.headers.get("X-Cache") == "HIT"

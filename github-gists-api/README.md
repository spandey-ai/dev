
# Business Requirements:
    - Build an API, test it, and package it into a container
    - Build a simple HTTP web server API in any general-purpose programming language1 that interacts with the GitHub API and responds to requests on /<USER> with a list of the user’s publicly available Gists2.
    - Create an automated test to validate that your web server API works. An example user to use as test data is octocat.-
    - Package the web server API into a docker container that listens for requests on port 8080. You do not need to publish the resulting container image in any container registry, but we are expecting the Dockerfile in the submission.
    - The solution may optionally provide other functionality (e.g. pagination, caching) but the above must be implemented.

```
# GitHub Gists API (Flask HTTP Server)

A simple Flask-based HTTP API to fetch a GitHub user’s **public gists** and return them as JSON.  

- **Endpoint**: `GET /<username>`  
- **Query params**:  
  - `page` (default: `1`)  
  - `per_page` (default: `30`, allowed range: `1–100`)  
- **Port**: `8080`  
- **Extras**:  
  - Basic error handling  
  - Optional in-memory caching with TTL  
  - Health check endpoint at `/healthz`  

---

## 📂 Project Structure
```

github-gists-api/
│
├── app.py               # Main Flask application
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker build instructions
├── README.md            # Project documentation
│
├── tests/               # Automated tests (pytest)
│   └── test_app.py
│   └── listuser.py      # Fetch the list of Gist user for testing 
│
└── .venv/               # Virtual environment (optional, local only)

````

---

## Setup

### 1. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server (development mode)

```bash
export FLASK_ENV=development
python app.py
```

The server will start on **[http://localhost:8080](http://localhost:8080)**.

### 4. Test with curl

```bash
# macOS / Linux
curl -s http://localhost:8080/octocat | jq .

# Windows
curl.exe -s http://localhost:8080/octocat | jq .
curl.exe -s http://localhost:8080/akbar70101 | jq .
curl.exe -s "http://localhost:8080/octocat?page=2&per_page=30" | jq .
```

### Optional environment variables

* `GIST_CACHE_TTL` → cache time-to-live in seconds (default: `60`)
* `GITHUB_TOKEN` → personal access token for higher GitHub API rate limits

---

## Running Tests

Tests use `pytest` with mocked GitHub responses (no network needed).

```bash
python3 -m pytest -q
```

Example output:

```
.....                                                                                                            [100%]
5 passed in 0.55s
```

---

## Docker

### Build the image

```bash
docker build -t gists-api:latest .
```

### Run the container

```bash
docker run --rm -p 8080:8080 gists-api:latest
docker run --rm -dp 8080:8080 gists-api:latest   # detached mode
```

### Example request

```bash
# Linux / macOS
curl -s http://localhost:8080/octocat | jq .

# Windows
curl.exe -v "http://localhost:8080/octocat" | jq
```

---

## API Endpoints

### `GET /<username>`

Returns JSON with gist details:

```jsonc
{
  "user": "octocat",
  "page": 1,
  "per_page": 30,
  "count": 1,
  "gists": [
    {
      "id": "aa5a315d61ae9438b18d",
      "description": "Hello world gist",
      "html_url": "https://gist.github.com/aa5a315d61ae9438b18d",
      "files": ["hello_world.py"],
      "public": true,
      "created_at": "2021-01-01T00:00:00Z",
      "updated_at": "2021-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "next": null,
    "prev": null,
    "first": 1,
    "last": null
  }
}
```

---

### `GET /healthz`

Simple health check:

```json
{"status": "ok"}
```

---

## Notes

* Pagination is inferred from GitHub’s `Link` header (if available).
* Usernames are validated against GitHub’s rules.
* Error codes:

  * `429` → rate limited
  * `404` → user not found
  * `502` → GitHub upstream error

---

## 🔗 Direct GitHub API (reference)

```bash
curl "https://api.github.com/gists/public?page=1&per_page=100"
```

```

---
```
## AI based implementation
'''
curl https://api.github.com/gists/public?page=1?per_page=100

There are number of options, we can achieve this solution with low code implementation. I am listing few other framework to implement above stated requirements:
Option 2: Azure Databricks
Option 3: ADF solution/Storage Account+App Services
Option 4: FastAPI
Option 5: LogicaApps--->Azure AI Search--->Azure AI foundry Chatbot
'''
import requests
from collections import Counter

user_counts = Counter()

for page in range(1, 11):  # Fetch 10 pages = 1000 gists
    url = f"https://api.github.com/gists/public?page={page}&per_page=100"
    response = requests.get(url)
    gists = response.json()
    for gist in gists:
        if gist.get("owner"):
            user = gist["owner"]["login"]
            user_counts[user] += 1

# Top 10 users by gist count
for user, count in user_counts.most_common(10):
    print(f"{user}: {count} gists")
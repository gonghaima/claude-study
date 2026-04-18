import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import requests
from settings import API_URL, MODEL, HEADERS, PROVIDER

payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "What is quantum computing? Answer in one sentence"}],
}

if PROVIDER == "openrouter":
    pass
else:
    payload["stream"] = False

response = requests.post(API_URL, headers=HEADERS, json=payload)
response.raise_for_status()

if PROVIDER == "openrouter":
    print(response.json()["choices"][0]["message"]["content"])
else:
    print(response.json()["message"]["content"])

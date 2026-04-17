import requests

model = "gemma4:e4b"

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "What is quantum computing? Answer in one sentence"
            }
        ],
        "stream": False
    }
)

print(response.json()["message"]["content"])

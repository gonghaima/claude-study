import requests

model = "gemma4:e4b"


def chat(messages, system=None, temperature=1.0):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }

    if system:
        payload["system"] = system

    response = requests.post("http://localhost:11434/api/chat", json=payload)
    return response.json()["message"]["content"]


messages = [{"role": "user", "content": "Give me a one-sentence movie idea."}]

print("Low temperature (0.0) - predictable:")
answer = chat(messages, temperature=0.0)
print(answer)

print("\nHigh temperature (1.0) - creative:")
answer = chat(messages, temperature=1.0)
print(answer)

import requests
from settings import API_URL, MODEL, HEADERS, PROVIDER


def chat(messages, temperature=1.0):
    payload = {"model": MODEL, "messages": messages}

    if PROVIDER == "openrouter":
        payload["temperature"] = temperature
    else:  # ollama
        payload["stream"] = False
        payload["options"] = {"temperature": temperature}

    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()

    if PROVIDER == "openrouter":
        return response.json()["choices"][0]["message"]["content"]
    else:
        return response.json()["message"]["content"]


messages = [{"role": "user", "content": "Give me a one-sentence movie idea."}]

print("Low temperature (0.0) - predictable:")
print(chat(messages, temperature=0.0))

print("\nHigh temperature (1.0) - creative:")
print(chat(messages, temperature=1.0))

import requests
from settings import API_URL, MODEL, HEADERS, PROVIDER


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, stop_sequences=None):
    payload = {"model": MODEL, "messages": messages}
    if PROVIDER == "ollama":
        payload["stream"] = False
    if stop_sequences:
        payload["stop"] = stop_sequences

    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()

    if PROVIDER == "openrouter":
        return response.json()["choices"][0]["message"]["content"]
    else:
        return response.json()["message"]["content"]


messages = []
prompt = """Generate three different sample AWS CLI commands. Each should be very short."""
add_user_message(messages, prompt)
add_assistant_message(messages, "Here are all three commands in a single block without any comments:\n```bash")
text = chat(messages, stop_sequences=["```"])

print(text.strip())

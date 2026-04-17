import requests
from settings import API_URL, MODEL, HEADERS, PROVIDER


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages):
    payload = {"model": MODEL, "messages": messages}
    if PROVIDER == "ollama":
        payload["stream"] = False

    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()

    if PROVIDER == "openrouter":
        return response.json()["choices"][0]["message"]["content"]
    else:
        return response.json()["message"]["content"]


messages = []

while True:
    user_input = input("You: ")
    add_user_message(messages, user_input)
    response = chat(messages)
    add_assistant_message(messages, response)
    print(f"Bot: {response}")

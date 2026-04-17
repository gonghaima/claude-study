import requests

model = "gemma4:e4b"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages):
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False
        }
    )
    return response.json()["message"]["content"]


messages = []

while True:
    user_input = input("You: ")
    add_user_message(messages, user_input)
    response = chat(messages)
    add_assistant_message(messages, response)
    print(f"Bot: {response}")

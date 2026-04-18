import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
import time
import requests
from settings import API_URL, MODEL, HEADERS, PROVIDER


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def stream_chat(messages, retries=3):
    payload = {"model": MODEL, "messages": messages, "stream": True}

    for attempt in range(retries):
        response = requests.post(API_URL, headers=HEADERS, json=payload, stream=True)
        if response.status_code == 429:
            wait = 2 ** attempt
            print(f"Rate limited. Retrying in {wait}s...")
            time.sleep(wait)
            continue
        response.raise_for_status()
        break
    else:
        print("Rate limit exceeded after retries. Please wait and try again.")
        return

    if PROVIDER == "openrouter":
        # OpenRouter sends Server-Sent Events: "data: {...}\n\n"
        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[len("data: "):]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    print(delta, end="", flush=True)
    else:  # ollama
        # Ollama sends newline-delimited JSON objects
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line.decode("utf-8"))
            delta = chunk.get("message", {}).get("content", "")
            if delta:
                print(delta, end="", flush=True)
            if chunk.get("done"):
                break

    print()  # newline after stream ends


messages = []
add_user_message(messages, "Write a short poem about the ocean")

print(f"Streaming with {PROVIDER}...\n")
stream_chat(messages)

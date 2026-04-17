import os
import requests
from dotenv import load_dotenv

load_dotenv()

model = "google/gemma-4-26b-a4b-it:free"
api_key = os.environ.get("OPENROUTER_API_KEY")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
}


def chat(messages, temperature=1.0):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


messages = [{"role": "user", "content": "Give me a one-sentence movie idea."}]

print("Low temperature (0.0) - predictable:")
answer = chat(messages, temperature=0.0)
print(answer)

print("\nHigh temperature (1.0) - creative:")
answer = chat(messages, temperature=1.0)
print(answer)

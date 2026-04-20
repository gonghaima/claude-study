import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
import requests
from settings import API_URL, MODEL, HEADERS, PROVIDER


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, temperature=1.0, stop_sequences=[]):
    payload = {"model": MODEL, "messages": messages, "temperature": temperature}
    if PROVIDER == "ollama":
        payload["stream"] = False
        payload["options"] = {"temperature": temperature}
        del payload["temperature"]
        if stop_sequences:
            payload["options"]["stop"] = stop_sequences
    elif stop_sequences:
        payload["stop"] = stop_sequences

    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()

    if PROVIDER == "openrouter":
        return response.json()["choices"][0]["message"]["content"]
    else:
        return response.json()["message"]["content"]


def generate_dataset():
    prompt = """
Generate an evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts that generate Python, JSON, or Regex specifically for AWS-related tasks. Generate an array of JSON objects, each representing task that requires Python, JSON, or a Regex to complete.

Example output:
```json
[
  {
    "task": "Description of task",
    "format": "json" or "python" or "regex",
    "solution_criteria": "Key criteria for evaluating the solution"
  },
  ...additional
]
```

* Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a single regex
* Focus on tasks that do not require writing much code

Please generate 3 objects.
"""
    messages = []
    add_user_message(messages, prompt)
    if PROVIDER == "openrouter":
        add_assistant_message(messages, "```json")
        text = chat(messages, stop_sequences=["```"])
    else:
        text = chat(messages)
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        else:
            text = text.strip()
    return json.loads(text)


dataset = generate_dataset()
print(dataset)

with open(os.path.join(os.path.dirname(__file__), "dataset.json"), "w") as f:
    json.dump(dataset, f, indent=2)

print("\nDataset saved to dataset.json")

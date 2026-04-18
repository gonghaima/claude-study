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


def run_prompt(test_case):
    """Merges the prompt and test case input, then returns the result"""
    prompt = f"""
Please solve the following task:

{test_case["task"]}
"""
    messages = []
    add_user_message(messages, prompt)
    output = chat(messages)
    return output


def run_test_case(test_case):
    """Calls run_prompt, then grades the result"""
    output = run_prompt(test_case)

    # TODO - Grading
    score = 10

    return {
        "output": output,
        "test_case": test_case,
        "score": score,
    }


def run_eval(dataset):
    """Loads the dataset and calls run_test_case with each case"""
    results = []

    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)

    return results


with open(os.path.join(os.path.dirname(__file__), "dataset.json"), "r") as f:
    dataset = json.load(f)

results = run_eval(dataset)
print(json.dumps(results, indent=2))

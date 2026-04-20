import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import ast
import json
import re
import requests
from statistics import mean
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

* Respond only with Python, JSON, or a plain Regex
* Do not add any comments or commentary or explanation
"""
    messages = []
    add_user_message(messages, prompt)
    output = chat(messages)
    return output


def validate_json(text):
    try:
        json.loads(text.strip())
        return 10
    except json.JSONDecodeError:
        return 0


def validate_python(text):
    try:
        ast.parse(text.strip())
        return 10
    except SyntaxError:
        return 0


def validate_regex(text):
    try:
        re.compile(text.strip())
        return 10
    except re.error:
        return 0


def grade_syntax(response, test_case):
    fmt = (test_case.get("format") or test_case.get("required_artifact_type", "")).lower()
    if "json" in fmt:
        return validate_json(response)
    elif "python" in fmt:
        return validate_python(response)
    else:
        return validate_regex(response)


def grade_by_model(test_case, output):
    eval_prompt = f"""
You are an expert AWS code reviewer. Your task is to evaluate the following AI-generated solution.

Original Task:
<task>
{test_case["task"]}
</task>

Solution to Evaluate:
<solution>
{output}
</solution>

Criteria you should use to evaluate the solution:
<criteria>
{test_case.get("solution_criteria", "Evaluate correctness, clarity, and adherence to AWS best practices.")}
</criteria>

Output Format
Provide your evaluation as a structured JSON object with the following fields, in this specific order:
- "strengths": An array of 1-3 key strengths
- "weaknesses": An array of 1-3 key areas for improvement
- "reasoning": A concise explanation of your overall assessment
- "score": A number between 1-10

Respond with JSON. Keep your response concise and direct.
Example response shape:
{{
    "strengths": string[],
    "weaknesses": string[],
    "reasoning": string,
    "score": number
}}
    """

    for attempt in range(3):
        messages = []
        add_user_message(messages, eval_prompt)
        eval_text = chat(messages)
        if eval_text is None:
            continue
        # Strip markdown code block if present
        if "```" in eval_text:
            eval_text = eval_text.split("```")[1]
            if eval_text.startswith("json"):
                eval_text = eval_text[4:]
        try:
            return json.loads(eval_text.strip())
        except json.JSONDecodeError:
            continue
    raise RuntimeError("grade_by_model: failed to get valid JSON from API after 3 attempts")


def run_test_case(test_case):
    """Calls run_prompt, then grades the result"""
    output = run_prompt(test_case)

    model_grade = grade_by_model(test_case, output)
    model_score = model_grade["score"]
    reasoning = model_grade["reasoning"]

    syntax_score = grade_syntax(output, test_case)
    score = (model_score + syntax_score) / 2

    return {
        "output": output,
        "test_case": test_case,
        "score": score,
        "reasoning": reasoning,
    }


def run_eval(dataset):
    """Loads the dataset and calls run_test_case with each case"""
    results = []

    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)

    average_score = mean([result["score"] for result in results])
    print(f"Average score: {average_score}")

    return results


with open(os.path.join(os.path.dirname(__file__), "dataset.json"), "r") as f:
    dataset = json.load(f)

results = run_eval(dataset)
print(json.dumps(results, indent=2))

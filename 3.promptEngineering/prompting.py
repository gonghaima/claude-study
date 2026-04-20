import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
import re
import requests
import concurrent.futures
from textwrap import dedent
from statistics import mean
from settings import API_URL, MODEL, HEADERS, PROVIDER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, system=None, temperature=1.0, stop_sequences=[]):
    all_messages = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)

    payload = {"model": MODEL, "messages": all_messages, "temperature": temperature}

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


def parse_json_response(text):
    """Parse JSON from a model response, stripping markdown fences if present."""
    if text is None:
        return None
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def chat_json(messages, system=None, temperature=1.0, retries=3):
    """Call chat and parse the result as JSON, retrying on failure."""
    for _ in range(retries):
        text = chat(messages, system=system, temperature=temperature)
        if text is None:
            continue
        try:
            return parse_json_response(text)
        except (json.JSONDecodeError, ValueError):
            continue
    raise RuntimeError("Failed to get valid JSON from API after retries")


# ---------------------------------------------------------------------------
# HTML Report
# ---------------------------------------------------------------------------

def generate_prompt_evaluation_report(evaluation_results):
    total_tests = len(evaluation_results)
    scores = [result["score"] for result in evaluation_results]
    avg_score = mean(scores) if scores else 0
    pass_rate = (
        100 * len([s for s in scores if s >= 7]) / total_tests if total_tests else 0
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Prompt Evaluation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary-stats {{ display: flex; gap: 10px; flex-wrap: wrap; }}
        .stat-box {{ background: #fff; border-radius: 5px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,.1); flex-basis: 30%; min-width: 200px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background-color: #4a4a4a; color: white; text-align: left; padding: 12px; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; vertical-align: top; width: 20%; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .score {{ font-weight: bold; padding: 5px 10px; border-radius: 3px; display: inline-block; }}
        .score-high {{ background-color: #c8e6c9; color: #2e7d32; }}
        .score-medium {{ background-color: #fff9c4; color: #f57f17; }}
        .score-low {{ background-color: #ffcdd2; color: #c62828; }}
        pre {{ background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 10px;
               font-family: monospace; font-size: 13px; white-space: pre-wrap; word-wrap: break-word; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Prompt Evaluation Report</h1>
        <div class="summary-stats">
            <div class="stat-box"><div>Total Test Cases</div><div class="stat-value">{total_tests}</div></div>
            <div class="stat-box"><div>Average Score</div><div class="stat-value">{avg_score:.1f} / 10</div></div>
            <div class="stat-box"><div>Pass Rate (≥7)</div><div class="stat-value">{pass_rate:.1f}%</div></div>
        </div>
    </div>
    <table>
        <thead>
            <tr>
                <th>Scenario</th><th>Prompt Inputs</th><th>Solution Criteria</th>
                <th>Output</th><th>Score</th><th>Reasoning</th>
            </tr>
        </thead>
        <tbody>
"""

    for result in evaluation_results:
        prompt_inputs_html = "<br>".join(
            f"<strong>{k}:</strong> {v}"
            for k, v in result["test_case"]["prompt_inputs"].items()
        )
        criteria_string = "<br>• ".join(result["test_case"]["solution_criteria"])
        score = result["score"]
        score_class = "score-high" if score >= 8 else ("score-low" if score <= 5 else "score-medium")

        html += f"""
            <tr>
                <td>{result["test_case"]["scenario"]}</td>
                <td>{prompt_inputs_html}</td>
                <td>• {criteria_string}</td>
                <td><pre>{result["output"]}</pre></td>
                <td><span class="score {score_class}">{score}</span></td>
                <td>{result["reasoning"]}</td>
            </tr>
"""

    html += "        </tbody>\n    </table>\n</body>\n</html>\n"
    return html


# ---------------------------------------------------------------------------
# PromptEvaluator
# ---------------------------------------------------------------------------

class PromptEvaluator:
    def __init__(self, max_concurrent_tasks=3):
        self.max_concurrent_tasks = max_concurrent_tasks

    def render(self, template_string, variables):
        result = template_string
        for key, value in variables.items():
            result = result.replace("{" + key + "}", str(value))
        return result.replace("{{", "{").replace("}}", "}")

    def generate_unique_ideas(self, task_description, prompt_inputs_spec, num_cases):
        example_prompt_inputs = "".join(
            f'"{k}": str # {v.replace(chr(10), " ")},'
            for k, v in prompt_inputs_spec.items()
        )

        prompt = self.render(dedent("""
            Generate {num_cases} unique, diverse ideas for testing a prompt that accomplishes this task:

            <task_description>
            {task_description}
            </task_description>

            The prompt will receive the following inputs:
            <prompt_inputs>
            {prompt_inputs_spec}
            </prompt_inputs>

            Each idea should represent a distinct scenario that tests different aspects of the task.

            Output a JSON array of brief scenario descriptions:
            ["idea 1", "idea 2", ...]

            Ensure each idea is distinct, relevant, specific, and solvable in under 400 tokens.
            Generate exactly {num_cases} ideas.
        """), {
            "num_cases": str(num_cases),
            "task_description": task_description,
            "prompt_inputs_spec": example_prompt_inputs,
        })

        system = "You are a test scenario designer specialized in creating diverse, unique testing scenarios."
        messages = []
        add_user_message(messages, prompt)
        return chat_json(messages, system=system, temperature=1.0)

    def generate_test_case(self, task_description, idea, prompt_inputs_spec={}):
        example_prompt_inputs = "".join(
            f'"{k}": "EXAMPLE_VALUE", // {v.replace(chr(10), " ")}\n'
            for k, v in prompt_inputs_spec.items()
        )
        allowed_keys = ", ".join(f'"{k}"' for k in prompt_inputs_spec.keys())

        prompt = self.render(dedent("""
            Generate a single detailed test case for a prompt evaluation based on:

            <task_description>
            {task_description}
            </task_description>

            <specific_idea>
            {idea}
            </specific_idea>

            <allowed_input_keys>
            {allowed_keys}
            </allowed_input_keys>

            Output as JSON:
            {
                "prompt_inputs": {
                    {example_prompt_inputs}
                },
                "solution_criteria": ["criterion 1", "criterion 2"]
            }

            IMPORTANT:
            - ONLY use these exact keys in prompt_inputs: {allowed_keys}
            - All allowed keys must be present
            - Keep solution criteria concise (1-4 items), tied directly to the task
            - Solvable in under 400 tokens
        """), {
            "task_description": task_description,
            "idea": idea,
            "allowed_keys": allowed_keys,
            "example_prompt_inputs": example_prompt_inputs,
        })

        system = "You are a test case creator specializing in designing evaluation scenarios."
        messages = []
        add_user_message(messages, prompt)
        test_case = chat_json(messages, system=system, temperature=0.7)
        test_case["task_description"] = task_description
        test_case["scenario"] = idea
        return test_case

    def generate_dataset(
        self,
        task_description,
        prompt_inputs_spec={},
        num_cases=3,
        output_file="dataset.json",
    ):
        ideas = self.generate_unique_ideas(task_description, prompt_inputs_spec, num_cases)

        dataset = []
        completed = 0
        total = len(ideas)
        last_reported = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_tasks) as executor:
            futures = {
                executor.submit(self.generate_test_case, task_description, idea, prompt_inputs_spec): idea
                for idea in ideas
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    dataset.append(future.result())
                    completed += 1
                    pct = (completed // max(1, total // 5)) * 20
                    if pct > last_reported:
                        print(f"Generated {completed}/{total} test cases")
                        last_reported = pct
                except Exception as e:
                    print(f"Error generating test case: {e}")

        with open(output_file, "w") as f:
            json.dump(dataset, f, indent=2)

        return dataset

    def grade_output(self, test_case, output, extra_criteria=None):
        prompt_inputs = "".join(
            f'"{k}":"{v.replace(chr(10), " ")}",\n'
            for k, v in test_case["prompt_inputs"].items()
        )

        extra_criteria_section = ""
        if extra_criteria:
            extra_criteria_section = dedent(f"""
                Mandatory Requirements - ANY VIOLATION MEANS AUTOMATIC FAILURE (score of 3 or lower):
                <extra_important_criteria>
                {extra_criteria}
                </extra_important_criteria>
            """)

        eval_prompt = self.render(dedent("""
            Your task is to evaluate the following AI-generated solution with EXTREME RIGOR.

            Original task description:
            <task_description>
            {task_description}
            </task_description>

            Original task inputs:
            <task_inputs>
            { {prompt_inputs} }
            </task_inputs>

            Solution to Evaluate:
            <solution>
            {output}
            </solution>

            Criteria:
            <criteria>
            {solution_criteria}
            </criteria>

            {extra_criteria_section}

            Scoring:
            * 1-3: Fails mandatory requirements
            * 4-6: Meets mandatory but has significant gaps
            * 7-8: Meets all mandatory + most secondary criteria
            * 9-10: Meets all criteria

            Grade ONLY on listed criteria. Use the full 1-10 scale.

            Respond with JSON:
            {
                "strengths": string[],
                "weaknesses": string[],
                "reasoning": string,
                "score": number
            }
        """), {
            "task_description": test_case["task_description"],
            "prompt_inputs": prompt_inputs,
            "output": output,
            "solution_criteria": "\n".join(test_case["solution_criteria"]),
            "extra_criteria_section": extra_criteria_section,
        })

        messages = []
        add_user_message(messages, eval_prompt)
        return chat_json(messages, temperature=0.0)

    def run_test_case(self, test_case, run_prompt_function, extra_criteria=None):
        output = run_prompt_function(test_case["prompt_inputs"])
        grade = self.grade_output(test_case, output, extra_criteria)
        return {
            "output": output,
            "test_case": test_case,
            "score": grade["score"],
            "reasoning": grade["reasoning"],
        }

    def run_evaluation(
        self,
        run_prompt_function,
        dataset_file,
        extra_criteria=None,
        json_output_file="output.json",
        html_output_file="output.html",
    ):
        with open(dataset_file, "r") as f:
            dataset = json.load(f)

        results = []
        completed = 0
        total = len(dataset)
        last_reported = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_tasks) as executor:
            futures = {
                executor.submit(self.run_test_case, tc, run_prompt_function, extra_criteria): tc
                for tc in dataset
            }
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                completed += 1
                pct = (completed // max(1, total // 5)) * 20
                if pct > last_reported:
                    print(f"Graded {completed}/{total} test cases")
                    last_reported = pct

        avg = mean([r["score"] for r in results])
        print(f"Average score: {avg}")

        with open(json_output_file, "w") as f:
            json.dump(results, f, indent=2)

        html = generate_prompt_evaluation_report(results)
        with open(html_output_file, "w", encoding="utf-8") as f:
            f.write(html)

        return results


# ---------------------------------------------------------------------------
# Example: athlete meal plan (from tutorial)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    evaluator = PromptEvaluator(max_concurrent_tasks=1)

    dataset_file = os.path.join(os.path.dirname(__file__), "dataset.json")

    print("Generating dataset...")
    evaluator.generate_dataset(
        task_description="Write a compact, concise 1 day meal plan for a single athlete",
        prompt_inputs_spec={
            "height": "Athlete's height in cm",
            "weight": "Athlete's weight in kg",
            "goal": "Goal of the athlete",
            "restrictions": "Dietary restrictions of the athlete",
        },
        output_file=dataset_file,
        num_cases=3,
    )

    def run_prompt(prompt_inputs):
        prompt = f"""
What should this person eat?

- Height: {prompt_inputs["height"]}
- Weight: {prompt_inputs["weight"]}
- Goal: {prompt_inputs["goal"]}
- Dietary restrictions: {prompt_inputs["restrictions"]}
"""
        messages = []
        add_user_message(messages, prompt)
        return chat(messages)

    print("\nRunning evaluation...")
    output_dir = os.path.dirname(__file__)
    evaluator.run_evaluation(
        run_prompt_function=run_prompt,
        dataset_file=dataset_file,
        extra_criteria="""
The output should include:
- Daily caloric total
- Macronutrient breakdown
- Meals with exact foods, portions, and timing
""",
        json_output_file=os.path.join(output_dir, "output.json"),
        html_output_file=os.path.join(output_dir, "output.html"),
    )

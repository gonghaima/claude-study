# Accessing Claude with the API

A collection of Python scripts demonstrating how to interact with LLMs via REST APIs, supporting both [OpenRouter](https://openrouter.ai) and local [Ollama](https://ollama.com) as providers.

## Scripts

| Script | Description |
|---|---|
| `1.accessingClaudeWithTheAPI/main.py` | Single-turn request — sends one prompt and prints the response |
| `1.accessingClaudeWithTheAPI/multi_turn.py` | Multi-turn script — sends a fixed two-turn conversation |
| `1.accessingClaudeWithTheAPI/chatbot.py` | Interactive chatbot — REPL loop that lets you chat in real time |
| `1.accessingClaudeWithTheAPI/streaming.py` | Streaming responses — prints tokens as they arrive with retry on rate limits |
| `1.accessingClaudeWithTheAPI/temperature.py` | Temperature demo — compares low vs high temperature outputs |
| `1.accessingClaudeWithTheAPI/structured_data.py` | Structured data extraction — uses stop sequences to extract clean code blocks |
| `2.promptEvaluation/generate_dataset.py` | Dataset generation — generates a JSON evaluation dataset of AWS-related coding tasks |
| `2.promptEvaluation/run_eval.py` | Prompt evaluation — runs model-based and syntax-based grading across all dataset test cases |
| `3.promptEngineering/prompting.py` | Prompt engineering — iterative evaluator with concurrent dataset generation, model grading, and HTML report output |
| `4.tools/001_tools.py` | Tool use — agentic loop with `get_current_datetime`, `add_duration_to_datetime`, and `set_reminder` |

## Provider Configuration

All scripts share `settings.py` at the repo root. Switch providers via the `PROVIDER` env var:

```bash
PROVIDER=openrouter  # default, uses OpenRouter
PROVIDER=ollama      # uses local Ollama instance
```

## Requirements

- Python 3.x
- For OpenRouter: an `OPENROUTER_API_KEY` in your `.env` file
- For Ollama: [Ollama](https://ollama.com) installed and running with the `gemma4:e4b` model pulled

## Setup

1. Create and activate the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install requests python-dotenv
   ```

3. Create a `.env` file at the repo root:
   ```
   PROVIDER=openrouter
   OPENROUTER_API_KEY=your_key_here
   ```

## Run

```bash
venv/bin/python 1.accessingClaudeWithTheAPI/main.py
```

## Multi-Turn Conversations

`multi_turn.py` demonstrates how to maintain conversation history across multiple requests, allowing the model to reference previous messages.

### How It Works

A `messages` list accumulates the full conversation history. Each turn:
1. Append a user message with `add_user_message(messages, text)`
2. Send the full history via `chat(messages)`
3. Append the assistant's reply with `add_assistant_message(messages, text)`

The next request includes all prior turns, so the model has full context.

### Run

```bash
venv/bin/python 1.accessingClaudeWithTheAPI/multi_turn.py
```

## Interactive Chatbot

`chatbot.py` is a REPL-style chatbot that lets you chat with the model interactively. It uses the same conversation-history pattern as `multi_turn.py`, but driven by live user input instead of a hardcoded script.

### How It Works

1. Prompts you with `You: ` and reads your input
2. Appends it to `messages` and sends the full history to the model
3. Prints the response as `Bot: ...` and appends it to `messages`
4. Repeats indefinitely until you kill the process (`Ctrl+C`)

### Run

```bash
venv/bin/python 1.accessingClaudeWithTheAPI/chatbot.py
```

### Example Session

```
You: What is the capital of France?
Bot: The capital of France is Paris.
You: What language do they speak there?
Bot: The primary language spoken in Paris (and France) is French.
```

## Streaming

`streaming.py` streams the model's response token-by-token as it's generated, with exponential backoff retry on rate limits (HTTP 429).

### Run

```bash
venv/bin/python 1.accessingClaudeWithTheAPI/streaming.py
```

## Temperature

`temperature.py` demonstrates the effect of the `temperature` parameter by sending the same prompt twice — once at `0.0` (deterministic) and once at `1.0` (creative).

### Run

```bash
venv/bin/python 1.accessingClaudeWithTheAPI/temperature.py
```

## Structured Data Extraction

`structured_data.py` uses stop sequences to control the model's output format. It pre-fills the assistant turn with a code fence opener and stops generation at the closing fence, extracting only the code block content.

### Run

```bash
venv/bin/python 1.accessingClaudeWithTheAPI/structured_data.py
```

## Prompt Evaluation — Dataset Generation

`2.promptEvaluation/generate_dataset.py` generates a JSON evaluation dataset of AWS-related coding tasks (Python, JSON, or Regex). It uses the assistant prefill technique to reliably extract structured JSON output:

- **OpenRouter**: prefills the assistant turn with `` ```json `` and uses a stop sequence to capture only the JSON content
- **Ollama**: asks the model directly and strips any markdown fences from the response (Ollama models don't reliably support mid-conversation assistant prefill)

The dataset is saved to `2.promptEvaluation/dataset.json`.

### Run

```bash
venv/bin/python 2.promptEvaluation/generate_dataset.py
./venv/bin/python3 2.promptEvaluation/run_eval.py
```

## Prompt Engineering

`3.promptEngineering/prompting.py` implements a `PromptEvaluator` class for iterative prompt improvement. The workflow:

1. **Generate a dataset** — automatically creates diverse test cases for your prompt
2. **Run a baseline prompt** — evaluates a naive first attempt to establish a score
3. **Iterate** — apply prompt engineering techniques and re-run to measure improvement

The evaluator uses concurrent API calls, model-based grading with mandatory/secondary criteria, and produces both a JSON results file and a colour-coded HTML report.

### Run

```bash
./venv/bin/python3 3.promptEngineering/prompting.py
```

Output files are written to `3.promptEngineering/output.json` and `3.promptEngineering/output.html`.

## Tool Use

`4.tools/001_tools.py` demonstrates the full agentic tool-calling loop using the same `requests`-based setup as the other scripts. It defines three tools (`get_current_datetime`, `add_duration_to_datetime`, `set_reminder`) and runs them through an agentic loop that feeds tool results back to the model until it stops calling tools.

### Run

```bash
venv/bin/python 4.tools/001_tools.py
```

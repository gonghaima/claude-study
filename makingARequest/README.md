# Making a Request

A collection of Python scripts that interact with a local [Ollama](https://ollama.com) model via its REST API.

| Script | Description |
|---|---|
| `main.py` | Single-turn request — sends one prompt and prints the response |
| `multi_turn.py` | Multi-turn script — sends a fixed two-turn conversation |
| `chatbot.py` | Interactive chatbot — REPL loop that lets you chat in real time |

## How It Works

All scripts send requests to Ollama's local REST API (`http://localhost:11434/api/chat`) using the `gemma4:e4b` model.

## Requirements

- [Ollama](https://ollama.com) installed and running with the `gemma4:e4b` model pulled
- Python 3.x

## Setup

1. Create and activate the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install requests
   ```

## Run

```bash
python3 main.py
```

## Test

Change the `content` field in `main.py` to any prompt you like:

```python
"content": "Your prompt here"
```

Then re-run:

```bash
python3 main.py
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
python3 multi_turn.py
```

### Example Flow

```python
messages = []

add_user_message(messages, "Define quantum computing in one sentence")
answer = chat(messages)
add_assistant_message(messages, answer)

add_user_message(messages, "Write another sentence")
final_answer = chat(messages)
```

The second prompt ("Write another sentence") works because the model sees the first exchange in `messages`.

## Interactive Chatbot

`chatbot.py` is a REPL-style chatbot that lets you chat with the model interactively. It uses the same conversation-history pattern as `multi_turn.py`, but driven by live user input instead of a hardcoded script.

### How It Works

1. Prompts you with `You: ` and reads your input
2. Appends it to `messages` and sends the full history to the model
3. Prints the response as `Bot: ...` and appends it to `messages`
4. Repeats indefinitely until you kill the process (`Ctrl+C`)

### Run

```bash
python3 chatbot.py
```

### Example Session

```
You: What is the capital of France?
Bot: The capital of France is Paris.
You: What language do they speak there?
Bot: The primary language spoken in Paris (and France) is French.
```

Because the full `messages` list is sent each turn, the model retains context across the entire conversation.

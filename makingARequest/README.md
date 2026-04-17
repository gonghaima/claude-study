# Making a Request

A simple Python script that sends a prompt to a local [Ollama](https://ollama.com) model and prints the response.

## How It Works

`main.py` sends a chat request to Ollama's local REST API (`http://localhost:11434/api/chat`) using the `gemma4:e4b` model and prints the generated text.

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

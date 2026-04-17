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

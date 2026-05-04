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
| `4.tools/001_tools_007.py` | Multi-turn tool use — extended conversation loop with flexible message handlers and sequential tool chaining |
| `4.tools/003_tool_streaming.py` | Streaming tool use — streams tokens and tool call arguments in real time with a multi-turn conversation loop |
| `5.RAG/chunk/001_chunking.ipynb` | RAG chunking — text splitting strategies for retrieval-augmented generation |
| `5.RAG/embedding/002_embeddings.ipynb` | RAG embeddings — generating and comparing vector embeddings with VoyageAI |
| `5.RAG/RAGFlowImplementation/003_vectordb.ipynb` | Vector database — storing and querying embeddings for semantic search |
| `5.RAG/RAGFlowImplementation/004_bm25.ipynb` | BM25 retrieval — keyword-based retrieval as a complement to vector search |
| `5.RAG/RAGFlowImplementation/005_hybrid.ipynb` | Hybrid retrieval — combining vector and BM25 search with reciprocal rank fusion |
| `6.extendedThinking/001_thinking.ipynb` | Extended thinking — enabling and using Claude's extended reasoning mode |
| `7.imageSupport/002_images.ipynb` | Image support — sending images to the model and processing visual content |
| `8.citation/002_citations_complete.ipynb` | Citations — extracting and formatting citations from model responses |
| `9.codeExecution_fileAPI/005_code_execution.ipynb` | Code execution & File API — running code and working with uploaded files |
| `10.MCP/cli_project_mine/main.py` | MCP chat app — interactive CLI chat with document retrieval and MCP tool/prompt/resource support |

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
   pip install requests python-dotenv anthropic "mcp[cli]>=1.8.0" prompt-toolkit
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

## Multi-Turn Tool Use

`4.tools/001_tools_007.py` extends the tool use pattern to handle scenarios where the model needs to call multiple tools in sequence to answer a single question (e.g. "What day is 103 days from today?" requires getting today's date first, then adding the duration). Key additions:

- `add_user_message` / `add_assistant_message` accept strings, lists, or full message dicts
- `text_from_message` extracts readable text from an API response message
- `run_tools` separates tool execution from the conversation loop
- `run_conversation` loops until the model stops requesting tools, appending each assistant turn and tool result back into the message history

### Run

```bash
venv/bin/python 4.tools/001_tools_007.py
```

## Streaming Tool Use

`4.tools/003_tool_streaming.py` demonstrates streaming responses with tool calls using the same `requests`-based OpenRouter/Ollama setup. Tokens and tool call arguments are printed as they arrive. Key additions over the multi-turn script:

- `chat_stream` sends the request with `stream: true` and returns the raw response
- `parse_stream` decodes SSE lines (`data: {...}`) for OpenRouter or JSON lines for Ollama
- Tool call arguments are accumulated incrementally as deltas arrive and printed in real time
- Exponential backoff retry on 429 rate limit errors

**Note:** Tool calling requires a model that supports it. Set `OPENROUTER_MODEL` in your `.env` to a capable model (e.g. `google/gemma-4-31b-it:free`).

### Run

```bash
OPENROUTER_MODEL=google/gemma-4-31b-it:free venv/bin/python 4.tools/003_tool_streaming.py
```

## RAG — Retrieval-Augmented Generation

The `5.RAG/` folder covers the full RAG pipeline across three subfolders:

- **`chunk/`** — text splitting strategies (fixed-size, sentence, semantic)
- **`embedding/`** — generating vector embeddings with VoyageAI
- **`RAGFlowImplementation/`** — vector DB storage, BM25 keyword retrieval, and hybrid search combining both with reciprocal rank fusion

Open notebooks in Jupyter:

```bash
venv/bin/jupyter notebook 5.RAG/
```

## Extended Thinking

`6.extendedThinking/001_thinking.ipynb` demonstrates Claude's extended reasoning mode — enabling the model to think through complex problems step-by-step before responding.

## Image Support

`7.imageSupport/002_images.ipynb` demonstrates sending images to the model via the API and processing visual content in responses.

## Citations

`8.citation/002_citations_complete.ipynb` shows how to extract structured citations from model responses, linking claims back to source documents.

## Code Execution & File API

`9.codeExecution_fileAPI/005_code_execution.ipynb` demonstrates the code execution tool and File API — uploading files (e.g. `streaming.csv`) and having the model analyse them by running code.

## MCP Chat App

`10.MCP/cli_project_mine/` is a full CLI chat application using the Model Context Protocol (MCP). It uses OpenRouter or Ollama via `settings.py` and supports:

- Document retrieval with `@doc_id` syntax
- MCP prompt commands with `/command doc_id` syntax (Tab autocomplete)
- Extensible tools and resources defined in `mcp_server.py`

### Run the chat app

```bash
cd 10.MCP/cli_project_mine
../../venv/bin/python main.py
```

### Test the MCP client

Tests all client methods (`list_tools`, `call_tool`, `list_prompts`, `get_prompt`, `read_resource`) — no need to start the server separately:

```bash
cd 10.MCP/cli_project_mine
../../venv/bin/python mcp_client.py
```

### Debug with the MCP Inspector (browser UI)

```bash
cd 10.MCP/cli_project_mine
../../venv/bin/mcp dev mcp_server.py
```

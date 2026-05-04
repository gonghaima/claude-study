# MCP Chat

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models via OpenRouter or Ollama. It uses the shared `settings.py` at the repo root for provider/model configuration, and the MCP (Model Context Protocol) architecture for document retrieval, command-based prompts, and extensible tool integrations.

## Prerequisites

- Python 3.10+
- OpenRouter API key (or local Ollama instance)
- Shared `settings.py` and `.env` at the repo root (`claude-study/`)

## Setup

### Step 1: Configure the environment variables

Edit the root `.env` file (`claude-study/.env`):

```
PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=google/gemma-4-31b-it:free  # optional, needs tool-calling support
```

To use Ollama instead:

```
PROVIDER=ollama
OLLAMA_MODEL=gemma4:e4b
```

### Step 2: Install dependencies

From the **repo root** (`claude-study/`):

```bash
pip install -e 10.MCP/cli_project_mine/
```

Or install directly:

```bash
pip install requests "mcp[cli]>=1.8.0" prompt-toolkit python-dotenv
```

## Run the chat app

```bash
cd /path/to/claude-study/10.MCP/cli_project_mine
../../venv/bin/python main.py
```

### Usage

| Input | What it does |
|---|---|
| `Hello!` | Normal chat with the model |
| `@deposition.md` | Includes that document's content in your query |
| `/format deposition.md` | Runs the MCP `format` prompt (Tab autocompletes) |
| `Ctrl+C` | Exit |

## Test the MCP client

`mcp_client.py` has a `main()` that exercises all client methods against the live server. Run it directly — **no need to start the server separately**, the client spawns it automatically:

```bash
cd /path/to/claude-study/10.MCP/cli_project_mine
../../venv/bin/python mcp_client.py
```

This tests:
- `list_tools` — lists tools exposed by the server
- `call_tool` — reads and edits a document
- `list_prompts` — lists available prompt templates
- `get_prompt` — renders a prompt with arguments
- `read_resource` — lists all doc IDs and fetches a single doc's content

## Debug the MCP server (browser UI)

Use the MCP Inspector to explore tools, resources, and prompts interactively in a browser — no code changes needed:

```bash
cd /path/to/claude-study/10.MCP/cli_project_mine
../../venv/bin/mcp dev mcp_server.py
```

## Development

### Adding new documents

Edit the `docs` dictionary in `mcp_server.py`.

### Adding new tools / resources / prompts

Add decorated functions to `mcp_server.py` using `@mcp.tool()`, `@mcp.resource()`, or `@mcp.prompt()`.

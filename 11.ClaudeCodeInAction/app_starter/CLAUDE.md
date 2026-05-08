# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e .

# Run MCP server
uv run main.py

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_document.py::TestBinaryDocumentToMarkdown::test_binary_document_to_markdown_with_docx
```

## Architecture

This is an MCP (Model Context Protocol) server that exposes Python functions as tools to AI assistants.

- `main.py` — creates the `FastMCP` server instance, registers tools via `mcp.tool()(fn)`, and runs the server
- `tools/` — each module defines plain Python functions that are registered as MCP tools
- `tests/` — pytest tests; `tests/fixtures/` holds binary test files (`.docx`, `.pdf`)

**Data flow:** Binary document bytes + file extension → `tools/document.py:binary_document_to_markdown` → `MarkItDown` converts to markdown string.

## Defining MCP Tools

Tools are plain Python functions registered with:

```python
mcp.tool()(my_function)
```

Use `Field` from pydantic for parameter descriptions:

```python
from pydantic import Field

def my_tool(
    param1: str = Field(description="Detailed description of this parameter"),
    param2: int = Field(description="Explain what this parameter does"),
) -> ReturnType:
    """One-line summary.

    Detailed explanation of functionality.

    When to use:
    - Use case A
    - Use case B (not for X)

    Examples:
    >>> my_tool("foo", 42)
    "result"
    """
```

Tool docstrings should cover: summary, detailed behavior, when to use (and not use), and input/output examples.

## Code Style

Always apply appropriate types to function arguments.

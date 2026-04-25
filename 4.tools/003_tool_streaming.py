import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import time
import requests
from settings import API_URL, MODEL, HEADERS, PROVIDER


# ── Helper functions ──────────────────────────────────────────────────────────

def add_user_message(messages, message):
    """Accept a plain string or a list of blocks (e.g. tool results)."""
    messages.append({
        "role": "user",
        "content": message if isinstance(message, (str, list)) else message,
    })


def add_assistant_message(messages, message):
    """Accept the accumulated message dict built from streaming chunks."""
    messages.append(message)


def text_from_message(message):
    return message.get("content") or ""


# ── Tool schemas (OpenAI-compatible format) ───────────────────────────────────

save_article_schema = {
    "type": "function",
    "function": {
        "name": "save_article",
        "description": "Saves a scholarly journal article",
        "parameters": {
            "type": "object",
            "properties": {
                "abstract": {
                    "type": "string",
                    "description": "Abstract of the article. One short sentence max",
                },
                "meta": {
                    "type": "object",
                    "properties": {
                        "word_count": {
                            "type": "integer",
                            "description": "Word count",
                        },
                        "review": {
                            "type": "string",
                            "description": "Eight sentence review of the paper",
                        },
                    },
                    "required": ["word_count", "review"],
                },
            },
            "required": ["abstract", "meta"],
        },
    },
}

save_short_article_schema = {
    "type": "function",
    "function": {
        "name": "save_article",
        "description": "Saves a scholarly journal article",
        "parameters": {
            "type": "object",
            "properties": {
                "abstract": {
                    "type": "string",
                    "description": "Abstract of the article. One short sentence max",
                },
                "meta": {
                    "type": "object",
                    "properties": {
                        "word_count": {
                            "type": "integer",
                            "description": "Word count",
                        },
                        "review": {
                            "type": "string",
                            "description": "Review of paper. One short sentence max",
                        },
                    },
                    "required": ["word_count", "review"],
                },
            },
            "required": ["abstract", "meta"],
        },
    },
}


# ── Tool implementations ──────────────────────────────────────────────────────

def save_article(**kwargs):
    return "Article saved!"


def run_tool(tool_name, tool_input):
    if tool_name == "save_article":
        return save_article(**tool_input)
    raise ValueError(f"Unknown tool: {tool_name}")


def run_tools(tool_calls):
    """Execute all tool calls and return tool result messages."""
    results = []
    for tc in tool_calls:
        name = tc["function"]["name"]
        raw_args = tc["function"]["arguments"]
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        try:
            output = run_tool(name, args)
            results.append({
                "role": "tool",
                "tool_call_id": tc.get("id", name),
                "content": json.dumps(output),
            })
        except Exception as e:
            results.append({
                "role": "tool",
                "tool_call_id": tc.get("id", name),
                "content": f"Error: {e}",
            })
    return results


# ── Streaming chat ────────────────────────────────────────────────────────────

def chat_stream(messages, tools=None, tool_choice=None):
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1000,
        "stream": True,
    }
    if tools:
        payload["tools"] = tools
    if tool_choice:
        payload["tool_choice"] = tool_choice
    if PROVIDER == "ollama":
        payload["options"] = {}

    for attempt in range(5):
        response = requests.post(API_URL, headers=HEADERS, json=payload, stream=True)
        if response.status_code == 429:
            wait = 2 ** attempt
            print(f"[Rate limited, retrying in {wait}s...]")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response
    response.raise_for_status()


def parse_stream(response):
    """Yield parsed delta dicts from the streaming response."""
    for raw in response.iter_lines():
        if not raw:
            continue
        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw

        if PROVIDER == "ollama":
            yield json.loads(line)
        else:  # openrouter (SSE)
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                yield json.loads(data_str)


# ── Multi-turn conversation loop with streaming ───────────────────────────────

def run_conversation(messages, tools=[], tool_choice=None):
    """
    Stream responses and loop until the model stops calling tools.

    - Prints text tokens as they arrive
    - Prints tool call name and streaming arguments as they build up
    - Accumulates the full response to add to message history
    - Executes tool calls and feeds results back for the next turn
    """
    while True:
        response = chat_stream(messages, tools=tools, tool_choice=tool_choice)

        accumulated_content = ""
        accumulated_tool_calls = {}  # index -> tool call dict
        finish_reason = None

        for chunk in parse_stream(response):
            if PROVIDER == "ollama":
                delta_content = chunk.get("message", {}).get("content", "")
                if delta_content:
                    print(delta_content, end="", flush=True)
                    accumulated_content += delta_content

                if chunk.get("done"):
                    finish_reason = "stop"
                    tool_calls = chunk.get("message", {}).get("tool_calls")
                    if tool_calls:
                        finish_reason = "tool_calls"
                        for i, tc in enumerate(tool_calls):
                            fn_args = tc["function"]["arguments"]
                            accumulated_tool_calls[i] = {
                                "id": tc.get("id", f"call_{i}"),
                                "type": "function",
                                "function": {
                                    "name": tc["function"]["name"],
                                    "arguments": json.dumps(fn_args) if isinstance(fn_args, dict) else fn_args,
                                },
                            }
                            print(f'\n>>> Tool Call: "{tc["function"]["name"]}"')
                            print(json.dumps(fn_args, indent=2))

            else:  # openrouter (SSE / OpenAI-compatible)
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                choice = choices[0]
                delta = choice.get("delta", {})

                if delta.get("content"):
                    print(delta["content"], end="", flush=True)
                    accumulated_content += delta["content"]

                for tc_delta in delta.get("tool_calls", []):
                    idx = tc_delta["index"]
                    if idx not in accumulated_tool_calls:
                        accumulated_tool_calls[idx] = {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    if tc_delta.get("id"):
                        accumulated_tool_calls[idx]["id"] = tc_delta["id"]
                    fn = tc_delta.get("function", {})
                    if fn.get("name"):
                        accumulated_tool_calls[idx]["function"]["name"] += fn["name"]
                        print(f'\n>>> Tool Call: "{accumulated_tool_calls[idx]["function"]["name"]}"')
                    if fn.get("arguments"):
                        accumulated_tool_calls[idx]["function"]["arguments"] += fn["arguments"]
                        print(fn["arguments"], end="", flush=True)

                if choice.get("finish_reason"):
                    finish_reason = choice["finish_reason"]

        print("\n")

        tool_calls_list = [accumulated_tool_calls[k] for k in sorted(accumulated_tool_calls)]

        # Build the assistant message to store in history
        assistant_msg = {"role": "assistant", "content": accumulated_content or None}
        if tool_calls_list:
            assistant_msg["tool_calls"] = tool_calls_list

        add_assistant_message(messages, assistant_msg)

        if finish_reason != "tool_calls":
            break

        tool_results = run_tools(tool_calls_list)
        for result in tool_results:
            messages.append(result)

        if tool_choice:
            break

    return messages


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    messages = []
    add_user_message(messages, "Create and save a fake computer science article")
    run_conversation(messages, tools=[save_article_schema])

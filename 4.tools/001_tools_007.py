import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import requests
from datetime import datetime, timedelta
from settings import API_URL, MODEL, HEADERS, PROVIDER


# ── Helper functions ──────────────────────────────────────────────────────────

def add_user_message(messages, message):
    """Accept a plain string or a list of blocks (e.g. tool results)."""
    user_message = {
        "role": "user",
        "content": message if isinstance(message, (str, list)) else message,
    }
    messages.append(user_message)


def add_assistant_message(messages, message):
    """Accept a plain string or a full message dict from the API response."""
    if isinstance(message, dict):
        messages.append({"role": "assistant", "content": message.get("content"), "tool_calls": message["tool_calls"]} if message.get("tool_calls") else {"role": "assistant", "content": message.get("content")})
    else:
        messages.append({"role": "assistant", "content": message})


def text_from_message(message):
    """Extract the text content from an API response message dict."""
    return message.get("content") or ""


def chat(messages, tools=None):
    payload = {"model": MODEL, "messages": messages}

    if PROVIDER == "ollama":
        payload["stream"] = False
        if tools:
            payload["tools"] = tools
    else:  # openrouter
        if tools:
            payload["tools"] = tools

    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


def get_message(response):
    if PROVIDER == "ollama":
        return response["message"]
    return response["choices"][0]["message"]


def is_tool_call(message):
    return bool(message.get("tool_calls"))


def is_done(message):
    return not is_tool_call(message)


# ── Tool implementations ──────────────────────────────────────────────────────

def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty")
    return datetime.now().strftime(date_format)


def add_duration_to_datetime(datetime_str, duration=0, unit="days", input_format="%Y-%m-%d"):
    date = datetime.strptime(datetime_str, input_format)

    if unit == "seconds":
        new_date = date + timedelta(seconds=duration)
    elif unit == "minutes":
        new_date = date + timedelta(minutes=duration)
    elif unit == "hours":
        new_date = date + timedelta(hours=duration)
    elif unit == "days":
        new_date = date + timedelta(days=duration)
    elif unit == "weeks":
        new_date = date + timedelta(weeks=duration)
    elif unit == "months":
        month = date.month + duration
        year = date.year + month // 12
        month = month % 12
        if month == 0:
            month = 12
            year -= 1
        day = min(
            date.day,
            [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
             31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1],
        )
        new_date = date.replace(year=year, month=month, day=day)
    elif unit == "years":
        new_date = date.replace(year=date.year + duration)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")

    return new_date.strftime("%A, %B %d, %Y %I:%M:%S %p")


def set_reminder(content, timestamp):
    print(f"----\nSetting the following reminder for {timestamp}:\n{content}\n----")
    return f"Reminder set for {timestamp}: {content}"


# ── Tool schemas (OpenAI-compatible format) ───────────────────────────────────

get_current_datetime_schema = {
    "type": "function",
    "function": {
        "name": "get_current_datetime",
        "description": "Returns the current date and time formatted according to the specified format",
        "parameters": {
            "type": "object",
            "properties": {
                "date_format": {
                    "type": "string",
                    "description": "A string specifying the format of the returned datetime. Uses Python's strftime format codes.",
                }
            },
            "required": [],
        },
    },
}

add_duration_to_datetime_schema = {
    "type": "function",
    "function": {
        "name": "add_duration_to_datetime",
        "description": (
            "Adds a specified duration to a datetime string and returns the resulting datetime "
            "in a detailed format. Handles seconds, minutes, hours, days, weeks, months, and years. "
            "Output format: 'Thursday, April 03, 2025 10:30:00 AM'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "The input datetime string, formatted according to input_format.",
                },
                "duration": {
                    "type": "number",
                    "description": "Amount of time to add (can be negative). Defaults to 0.",
                },
                "unit": {
                    "type": "string",
                    "description": "One of: 'seconds', 'minutes', 'hours', 'days', 'weeks', 'months', 'years'. Defaults to 'days'.",
                },
                "input_format": {
                    "type": "string",
                    "description": "strptime format for parsing datetime_str. Defaults to '%Y-%m-%d'.",
                },
            },
            "required": ["datetime_str"],
        },
    },
}

set_reminder_schema = {
    "type": "function",
    "function": {
        "name": "set_reminder",
        "description": "Creates a timed reminder that will notify the user at the specified time with the provided content.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The reminder message text.",
                },
                "timestamp": {
                    "type": "string",
                    "description": "When to trigger the reminder (ISO 8601: YYYY-MM-DDTHH:MM:SS).",
                },
            },
            "required": ["content", "timestamp"],
        },
    },
}

ALL_TOOLS = [
    get_current_datetime_schema,
    add_duration_to_datetime_schema,
    set_reminder_schema,
]


# ── Tool dispatch ─────────────────────────────────────────────────────────────

def dispatch_tool(name, args):
    if name == "get_current_datetime":
        return get_current_datetime(**args)
    elif name == "add_duration_to_datetime":
        return add_duration_to_datetime(**args)
    elif name == "set_reminder":
        return set_reminder(**args)
    else:
        raise ValueError(f"Unknown tool: {name}")


# ── Tool runner ───────────────────────────────────────────────────────────────

def run_tools(message):
    """Execute all tool calls in a message and return tool result dicts."""
    tool_results = []
    for tc in message["tool_calls"]:
        name = tc["function"]["name"]
        # OpenRouter gives arguments as a JSON string; Ollama gives a dict
        raw_args = tc["function"]["arguments"]
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

        print(f"[Tool call] {name}({json.dumps(args)})")
        result = dispatch_tool(name, args)
        print(f"[Tool result] {result}\n")

        tool_results.append({
            "role": "tool",
            "tool_call_id": tc.get("id", name),
            "content": str(result),
        })
    return tool_results


# ── Multi-turn conversation loop ──────────────────────────────────────────────

def run_conversation(messages, tools=ALL_TOOLS):
    """
    Loop until the model stops requesting tools.

    Each iteration:
      1. Call the model with the current message history
      2. Append the assistant's response to history
      3. If it requested tools, run them and append results, then continue
      4. If it didn't request tools, we're done — return the final message
    """
    while True:
        response = chat(messages, tools=tools)
        message = get_message(response)

        add_assistant_message(messages, message)

        if is_done(message):
            break

        tool_results = run_tools(message)
        # Each tool result is its own message in OpenAI-compatible format
        for result in tool_results:
            messages.append(result)

    return message


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Requires two sequential tool calls:
    # Claude must first get today's date, then add 103 days to it.
    print("=" * 60)
    print("Demo: What day is 103 days from today?")
    print("=" * 60)
    messages = []
    add_user_message(messages, "What day is 103 days from today?")
    final = run_conversation(messages)
    print(f"Assistant: {text_from_message(final)}")

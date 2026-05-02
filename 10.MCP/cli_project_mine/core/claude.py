import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

import json
import requests
from settings import API_URL, MODEL, HEADERS, PROVIDER


class Claude:
    def __init__(self, model: str = MODEL):
        self.model = model

    def add_user_message(self, messages: list, message):
        """Accept a plain string or a list of blocks (e.g. tool results)."""
        messages.append({
            "role": "user",
            "content": message if isinstance(message, (str, list)) else message,
        })

    def add_assistant_message(self, messages: list, message):
        """Accept the message dict returned by get_message()."""
        messages.append(message)

    def get_message(self, response: dict) -> dict:
        """Extract the message dict from the API response."""
        if PROVIDER == "ollama":
            return response["message"]
        return response["choices"][0]["message"]

    def text_from_message(self, message: dict) -> str:
        return message.get("content") or ""

    def is_tool_call(self, message: dict) -> bool:
        return bool(message.get("tool_calls"))

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=[],
        tools=None,
    ) -> dict:
        payload = {
            "model": self.model,
            "max_tokens": 8000,
            "messages": messages,
        }

        if PROVIDER == "ollama":
            payload["stream"] = False
            payload["options"] = {"temperature": temperature}
            if stop_sequences:
                payload["options"]["stop"] = stop_sequences
        else:
            payload["temperature"] = temperature
            if stop_sequences:
                payload["stop"] = stop_sequences

        if tools:
            payload["tools"] = tools

        if system:
            # Prepend system as a system message (OpenAI-compatible)
            payload["messages"] = [{"role": "system", "content": system}] + list(messages)

        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()

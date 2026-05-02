import json
from typing import Optional
from mcp.types import CallToolResult, TextContent
from mcp_client import MCPClient


class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list:
        """Gets all tools from the provided clients in OpenAI-compatible format."""
        tools = []
        for client in clients.values():
            tool_models = await client.list_tools()
            tools += [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema,
                    },
                }
                for t in tool_models
            ]
        return tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        """Finds the first client that has the specified tool."""
        for client in clients:
            tools = await client.list_tools()
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                return client
        return None

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], message: dict
    ) -> list[dict]:
        """Execute tool calls and return tool result messages (OpenAI format)."""
        tool_calls = message.get("tool_calls", [])
        tool_result_messages = []

        for tc in tool_calls:
            tool_call_id = tc.get("id", tc["function"]["name"])
            tool_name = tc["function"]["name"]
            raw_args = tc["function"]["arguments"]
            tool_input = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            if not client:
                tool_result_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": "Could not find that tool",
                })
                continue

            try:
                tool_output: CallToolResult | None = await client.call_tool(
                    tool_name, tool_input
                )
                items = tool_output.content if tool_output else []
                content_list = [
                    item.text for item in items if isinstance(item, TextContent)
                ]
                tool_result_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(content_list),
                })
            except Exception as e:
                error_message = f"Error executing tool '{tool_name}': {e}"
                print(error_message)
                tool_result_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"error": error_message}),
                })

        return tool_result_messages

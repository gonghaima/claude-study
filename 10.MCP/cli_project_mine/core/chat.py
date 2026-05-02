from core.claude import Claude
from mcp_client import MCPClient
from core.tools import ToolManager


class Chat:
    def __init__(self, claude_service: Claude, clients: dict[str, MCPClient]):
        self.claude_service: Claude = claude_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(self, query: str) -> str:
        final_text_response = ""

        await self._process_query(query)

        while True:
            response = self.claude_service.chat(
                messages=self.messages,
                tools=await ToolManager.get_all_tools(self.clients),
            )

            message = self.claude_service.get_message(response)
            self.claude_service.add_assistant_message(self.messages, message)

            if self.claude_service.is_tool_call(message):
                print(self.claude_service.text_from_message(message))
                tool_results = await ToolManager.execute_tool_requests(
                    self.clients, message
                )
                for result in tool_results:
                    self.messages.append(result)
            else:
                final_text_response = self.claude_service.text_from_message(message)
                break

        return final_text_response

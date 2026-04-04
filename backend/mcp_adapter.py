import os
import sys
import json
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
from langchain_core.tools import Tool
from typing import Any, List

# Define the Stdio server parameters
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK_SERVER_SCRIPT = os.path.join(BASE_DIR, "mock_mcp_server.py")

server_params = StdioServerParameters(
    command=sys.executable, # Use current venv python
    args=[MOCK_SERVER_SCRIPT],
    env=None
)

async def execute_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Helper to call MCP server for a specific tool momentarily."""
    try:
        async with stdio_client(server_params) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                texts = []
                for content in result.content:
                    if content.type == "text":
                        texts.append(content.text)
                return "\n".join(texts)
    except Exception as e:
        return f"Error executing MCP tool {tool_name}: {str(e)}"

async def get_langchain_mcp_tools() -> List[Tool]:
    """
    Initializes a short-lived connection just to discover tools,
    then maps them to LangChain tools that will open individual connections when invoked.
    """
    lc_tools = []
    try:
        async with stdio_client(server_params) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                
                for mcp_tool in tools_response.tools:
                    def create_func(t_name=mcp_tool.name):
                        async def acall_tool(*args, **kwargs):
                            if len(args) == 1 and isinstance(args[0], str) and not kwargs:
                                try:
                                    kwargs = json.loads(args[0])
                                except:
                                    kwargs = {"query": args[0]}
                            elif len(args) == 1 and isinstance(args[0], dict):
                                kwargs = args[0]
                            return await execute_mcp_tool(t_name, kwargs)
                        return acall_tool
                    
                    lc_tools.append(
                        Tool(
                            name=mcp_tool.name,
                            description=mcp_tool.description,
                            coroutine=create_func(mcp_tool.name),
                            func=lambda *args, t_name=mcp_tool.name, **kwargs: asyncio.run(execute_mcp_tool(t_name, kwargs if kwargs else args[0] if args and isinstance(args[0], dict) else {"query": args[0]}))
                        )
                    )
    except Exception as e:
        print(f"Warning: Could not connect to MCP Server: {e}")
        
    return lc_tools

import json
import os
import uvicorn
from fastapi import FastAPI
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from pydantic import BaseModel
from typing import Any
from starlette.requests import Request
from mcp.types import Tool, TextContent
from mcp.server import NotificationOptions, Server

# Load the local config of human sentence rules
RULES_FILE = "mcp_rules.json"

def load_rules():
    if not os.path.exists(RULES_FILE):
        return []
    with open(RULES_FILE, "r") as f:
        return json.load(f)

# Initialize MCP Server
app = FastAPI(title="Mock External Validation MCP Server")

# Create the MCP Server instance
mcp_server = Server("MockValidator")

@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    Exposes a tool for querying external business rules.
    """
    return [
        Tool(
            name="get_external_business_rules",
            description="Fetch external business validation rules from the ERP or Vendor Management System based on the vendor or invoice context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string", "description": "The name of the vendor (if known) to get specific rules for."},
                    "invoice_type": {"type": "string", "description": "Type of invoice like 'services', 'hardware', etc."}
                },
                "required": []
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """
    Handles tool calls from the client.
    """
    if name == "get_external_business_rules":
        rules = load_rules()
        vendor_name = arguments.get("vendor_name", "").lower() if arguments else ""
        
        # Simple filtering for demo
        relevant_rules = []
        for r in rules:
            if vendor_name and vendor_name in r.lower():
                relevant_rules.append(r)
            elif not vendor_name:
                relevant_rules.append(r)
                
        if not relevant_rules:
             relevant_rules = rules # return all if no specific match
             
        combined_rules = "\n- ".join(relevant_rules)
        return [
            TextContent(
                type="text",
                text=f"External Business Rules from ERP:\n- {combined_rules}"
            )
        ]
    
    raise ValueError(f"Unknown tool: {name}")

import asyncio

if __name__ == "__main__":
    async def main():
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.run(
                read_stream, write_stream, mcp_server.create_initialization_options()
            )
            
    asyncio.run(main())

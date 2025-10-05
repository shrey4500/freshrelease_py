import os
import json
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

API_TOKEN = os.getenv("FRESHRELEASE_API_TOKEN")
BASE_URL = "https://freshworks.freshrelease.com"

server = Server("freshrelease-mcp-server")

async def make_request(project_key: str, endpoint: str, method: str = "GET", body: dict = None) -> dict:
    """Make HTTP request to Freshrelease API"""
    url = f"{BASE_URL}/{project_key}{endpoint}"
    headers = {
        "Authorization": f"Token {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=body)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=body)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Freshrelease tools"""
    return [
        Tool(
            name="freshrelease_get_users",
            description="Get all users in the Freshrelease project with pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination",
                        "default": 1
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of users per page",
                        "default": 30
                    }
                }
            }
        ),
        Tool(
            name="freshrelease_get_statuses",
            description="Get all statuses in the project",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="freshrelease_get_issue_types",
            description="Get all issue types available in the project",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="freshrelease_get_issue",
            description="Get a specific issue by its key (e.g., FBOTS-47941)",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key (e.g., FBOTS-47941)"
                    }
                },
                "required": ["issue_key"]
            }
        ),
        Tool(
            name="freshrelease_create_issue",
            description="Create a new issue in Freshrelease",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Issue title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description"
                    },
                    "issue_type_id": {
                        "type": "string",
                        "description": "Issue type ID (e.g., '14' for task)"
                    },
                    "owner_id": {
                        "type": "string",
                        "description": "Owner user ID"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project ID (e.g., '280')"
                    },
                    "custom_fields": {
                        "type": "object",
                        "description": "Custom fields as key-value pairs"
                    }
                },
                "required": ["title", "description", "issue_type_id", "owner_id", "project_id"]
            }
        ),
        Tool(
            name="freshrelease_update_issue",
            description="Update an existing Freshrelease issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key (e.g., FBOTS-48937)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Updated issue description"
                    },
                    "issue_type_id": {
                        "type": "string",
                        "description": "Issue type ID"
                    },
                    "custom_fields": {
                        "type": "object",
                        "description": "Custom fields to update"
                    }
                },
                "required": ["issue_key"]
            }
        ),
        Tool(
            name="freshrelease_get_comments",
            description="Get all comments on a specific issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "Issue ID (numeric, e.g., '2563487')"
                    }
                },
                "required": ["issue_id"]
            }
        ),
        Tool(
            name="freshrelease_add_comment",
            description="Add a comment to a specific issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "Issue ID (numeric, e.g., '2563487')"
                    },
                    "content": {
                        "type": "string",
                        "description": "Comment content"
                    }
                },
                "required": ["issue_id", "content"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "freshrelease_get_users":
            page = arguments.get("page", 1)
            result = await make_request(f"/users?page={page}")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "freshrelease_get_statuses":
            result = await make_request("/statuses")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "freshrelease_get_issue_types":
            result = await make_request("/issue_types")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "freshrelease_get_issue":
            issue_key = arguments["issue_key"]
            result = await make_request(f"/issues/{issue_key}")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "freshrelease_create_issue":
            body = {
                "issue": {
                    "title": arguments["title"],
                    "description": arguments["description"],
                    "key": PROJECT_KEY,
                    "issue_type_id": arguments["issue_type_id"],
                    "owner_id": arguments["owner_id"],
                    "project_id": arguments["project_id"],
                    "custom_field": arguments.get("custom_fields", {})
                }
            }
            result = await make_request("/issues", "POST", body)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "freshrelease_update_issue":
            issue_key = arguments["issue_key"]
            body = {"issue": {"key": issue_key}}
            
            if "description" in arguments:
                body["issue"]["description"] = arguments["description"]
            if "issue_type_id" in arguments:
                body["issue"]["issue_type_id"] = arguments["issue_type_id"]
            if "custom_fields" in arguments:
                body["issue"]["custom_field"] = arguments["custom_fields"]
            
            result = await make_request(f"/issues/{issue_key}", "PUT", body)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "freshrelease_get_comments":
            issue_id = arguments["issue_id"]
            result = await make_request(f"/issues/{issue_id}/comments")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "freshrelease_add_comment":
            issue_id = arguments["issue_id"]
            body = {"content": arguments["content"]}
            result = await make_request(f"/issues/{issue_id}/comments", "POST", body)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

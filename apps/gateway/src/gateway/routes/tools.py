"""Tools endpoints for managing and executing tools."""

from typing import Any

from fastapi import APIRouter, HTTPException
from mcp import FilesystemTool, GitTool, ShellTool, ToolRegistry
from pydantic import BaseModel

router = APIRouter(prefix="/tools", tags=["tools"])

# Global tool registry
_tool_registry = ToolRegistry()

# Register default tools
_tool_registry.register(FilesystemTool())
_tool_registry.register(GitTool())
_tool_registry.register(ShellTool())


class ToolExecuteRequest(BaseModel):
    """Request model for tool execution."""
    params: dict[str, Any]


@router.get("")
async def list_tools():
    """List all registered tools."""
    return {"tools": _tool_registry.list_tools()}


@router.get("/{tool_name}")
async def get_tool(tool_name: str):
    """Get tool information."""
    tools = _tool_registry.list_tools()
    for tool in tools:
        if tool["name"] == tool_name:
            return tool
    raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")


@router.post("/{tool_name}/execute")
async def execute_tool(tool_name: str, request: ToolExecuteRequest):
    """Execute a tool with given parameters."""
    try:
        result = await _tool_registry.execute(tool_name, request.params)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_tool(tool_name: str, tool_type: str):
    """Register a new tool instance."""
    if tool_type == "filesystem":
        tool = FilesystemTool()
    elif tool_type == "git":
        tool = GitTool()
    elif tool_type == "shell":
        tool = ShellTool()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool type: {tool_type}")

    _tool_registry.register(tool)
    return {"registered": tool_name, "type": tool_type}


@router.delete("/{tool_name}")
async def unregister_tool(tool_name: str):
    """Unregister a tool."""
    _tool_registry.unregister(tool_name)
    return {"unregistered": tool_name}

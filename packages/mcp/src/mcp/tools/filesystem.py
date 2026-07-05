"""Filesystem tool for file operations."""

from pathlib import Path
from typing import Any

from contracts import Tool, ToolResult


class FilesystemTool(Tool):
    """Tool for filesystem operations."""

    name = "filesystem"
    description = "Perform filesystem operations: read, write, list files"
    input_schema = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["read", "write", "list", "exists"],
                "description": "Operation to perform",
            },
            "path": {
                "type": "string",
                "description": "File or directory path",
            },
            "content": {
                "type": "string",
                "description": "Content to write (for write operation)",
            },
        },
        "required": ["operation", "path"],
    }

    def __init__(self, allowed_paths: list[str] | None = None):
        """Initialize filesystem tool.

        Args:
            allowed_paths: List of allowed base paths. If None, all paths allowed.
        """
        self.allowed_paths = allowed_paths

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is within allowed paths."""
        if not self.allowed_paths:
            return True

        abs_path = Path(path).resolve()
        for allowed in self.allowed_paths:
            abs_allowed = Path(allowed).resolve()
            try:
                abs_path.relative_to(abs_allowed)
                return True
            except ValueError:
                continue
        return False

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute filesystem operation."""
        operation = params.get("operation")
        path = params.get("path")

        if not operation or not path:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Missing required parameters: operation, path",
            )

        if not self._is_path_allowed(path):
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Path not allowed: {path}",
            )

        try:
            if operation == "read":
                return await self._read_file(path)
            elif operation == "write":
                content = params.get("content", "")
                return await self._write_file(path, content)
            elif operation == "list":
                return await self._list_directory(path)
            elif operation == "exists":
                return await self._check_exists(path)
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output=None,
                    error=f"Unknown operation: {operation}",
                )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=str(e),
            )

    async def _read_file(self, path: str) -> ToolResult:
        """Read file content."""
        file_path = Path(path)
        if not file_path.exists():
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"File not found: {path}",
            )

        if not file_path.is_file():
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Path is not a file: {path}",
            )

        content = file_path.read_text(encoding="utf-8")
        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"content": content, "size": len(content)},
        )

    async def _write_file(self, path: str, content: str) -> ToolResult:
        """Write content to file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"path": str(file_path), "size": len(content)},
        )

    async def _list_directory(self, path: str) -> ToolResult:
        """List directory contents."""
        dir_path = Path(path)
        if not dir_path.exists():
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Directory not found: {path}",
            )

        if not dir_path.is_dir():
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Path is not a directory: {path}",
            )

        entries = []
        for entry in dir_path.iterdir():
            entries.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else None,
            })

        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"entries": entries, "count": len(entries)},
        )

    async def _check_exists(self, path: str) -> ToolResult:
        """Check if path exists."""
        exists = Path(path).exists()
        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"exists": exists, "path": path},
        )

"""Git tool for version control operations."""

import subprocess
from typing import Any

from contracts import Tool, ToolResult


class GitTool(Tool):
    """Tool for git operations."""

    name = "git"
    description = "Perform git operations: status, diff, log, add, commit"
    input_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["status", "diff", "log", "add", "commit", "branch", "checkout"],
                "description": "Git command to execute",
            },
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Arguments for the git command",
            },
            "cwd": {
                "type": "string",
                "description": "Working directory for git command",
            },
        },
        "required": ["command"],
    }

    def __init__(self, allowed_paths: list[str] | None = None):
        """Initialize git tool.

        Args:
            allowed_paths: List of allowed working directories. If None, all paths allowed.
        """
        self.allowed_paths = allowed_paths

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is within allowed paths."""
        if not self.allowed_paths:
            return True

        from pathlib import Path
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
        """Execute git command."""
        command = params.get("command")
        args = params.get("args", [])
        cwd = params.get("cwd", ".")

        if not command:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Missing required parameter: command",
            )

        if not self._is_path_allowed(cwd):
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Path not allowed: {cwd}",
            )

        try:
            git_cmd = ["git", command] + args
            result = subprocess.run(
                git_cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    },
                )
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    },
                    error=f"Git command failed with return code {result.returncode}",
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Git command timed out",
            )
        except FileNotFoundError:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Git not found. Make sure git is installed and in PATH.",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=str(e),
            )

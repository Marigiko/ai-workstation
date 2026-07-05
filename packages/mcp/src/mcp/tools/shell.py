"""Shell tool for command execution with sandboxing."""

import subprocess
from typing import Any

from contracts import Tool, ToolResult


class ShellTool(Tool):
    """Tool for shell command execution with sandboxing."""

    name = "shell"
    description = "Execute shell commands with sandboxing"
    input_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute",
            },
            "cwd": {
                "type": "string",
                "description": "Working directory for command",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 30)",
            },
        },
        "required": ["command"],
    }

    # Dangerous commands that should be blocked
    BLOCKED_COMMANDS = {
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd if=/dev/zero",
        ":(){:|:&};:",  # Fork bomb
        "chmod -R 777 /",
        "chown -R",
        "> /dev/sda",
        "mv /",
        "shutdown",
        "reboot",
        "halt",
        "poweroff",
    }

    def __init__(
        self,
        allowed_paths: list[str] | None = None,
        blocked_commands: set[str] | None = None,
        timeout: int = 30,
    ):
        """Initialize shell tool.

        Args:
            allowed_paths: List of allowed working directories. If None, all paths allowed.
            blocked_commands: Set of blocked command patterns. If None, uses defaults.
            timeout: Default timeout in seconds.
        """
        self.allowed_paths = allowed_paths
        self.blocked_commands = blocked_commands or self.BLOCKED_COMMANDS
        self.default_timeout = timeout

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

    def _is_command_safe(self, command: str) -> bool:
        """Check if command is safe to execute."""
        command_lower = command.lower().strip()

        # Check for blocked commands
        for blocked in self.blocked_commands:
            if blocked in command_lower:
                return False

        # Check for dangerous patterns
        dangerous_patterns = [
            "sudo ",
            "su ",
            "| sudo",
            "| su",
            "eval ",
            "exec ",
        ]

        return all(pattern not in command_lower for pattern in dangerous_patterns)

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute shell command."""
        command = params.get("command")
        cwd = params.get("cwd", ".")
        timeout = params.get("timeout", self.default_timeout)

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

        if not self._is_command_safe(command):
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Command blocked for security reasons: {command}",
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
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
                    error=f"Command failed with return code {result.returncode}",
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Command timed out after {timeout} seconds",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=str(e),
            )

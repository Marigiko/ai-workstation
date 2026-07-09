"""Shell tool for command execution with sandboxing."""

import shlex
import subprocess
from pathlib import Path
from typing import Any

from contracts import Tool, ToolResult

# Commands that are always blocked regardless of arguments
BLOCKED_BINARIES = {
    "rm",
    "mkfs",
    "dd",
    "chmod",
    "chown",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "su",
    "sudo",
    "mount",
    "umount",
    "fdisk",
    "parted",
    "iptables",
    "ip6tables",
}


class ShellTool(Tool):
    """Tool for shell command execution with sandboxing."""

    name = "shell"
    description = "Execute shell commands with sandboxing"
    input_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute (will be split into arguments safely)",
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

    def __init__(
        self,
        allowed_paths: list[str] | None = None,
        allowed_commands: set[str] | None = None,
        blocked_commands: set[str] | None = None,
        timeout: int = 30,
    ):
        """Initialize shell tool.

        Args:
            allowed_paths: List of allowed working directories. If None, all paths allowed.
            allowed_commands: Set of allowed command binaries. If None, uses safe defaults.
            blocked_commands: Set of blocked command patterns. If None, uses defaults.
            timeout: Default timeout in seconds.
        """
        self.allowed_paths = allowed_paths
        self.allowed_commands = allowed_commands
        self.default_timeout = timeout

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

    def _parse_command(self, command: str) -> list[str] | None:
        """Safely parse command string into argument list.

        Returns None if command contains shell operators or is unsafe.
        """
        command = command.strip()
        if not command:
            return None

        # Block shell operators that enable injection
        dangerous_operators = ["|", "&&", "||", ";", ">", ">>", "<", "$(", "`", "\n"]
        for op in dangerous_operators:
            if op in command:
                return None

        try:
            return shlex.split(command)
        except ValueError:
            return None

    def _is_command_allowed(self, args: list[str]) -> bool:
        """Check if the parsed command is allowed."""
        if not args:
            return False

        # Get the base command name (without path)
        cmd = args[0]
        cmd_name = Path(cmd).name

        # Check against blocked binaries
        if cmd_name in BLOCKED_BINARIES:
            return False

        # If an allowlist is specified, check against it
        if self.allowed_commands is not None:
            return cmd_name in self.allowed_commands

        return True

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

        args = self._parse_command(command)
        if args is None:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Command contains unsafe shell operators and was blocked",
            )

        if not self._is_command_allowed(args):
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Command not allowed: {args[0]}",
            )

        try:
            result = subprocess.run(
                args,
                shell=False,
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

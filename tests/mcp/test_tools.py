"""Tests for MCP tools."""

import tempfile
from pathlib import Path

import pytest
from mcp import FilesystemTool, GitTool, ShellTool, ToolRegistry


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def tool_registry():
    """Create a tool registry with default tools."""
    registry = ToolRegistry()
    registry.register(FilesystemTool())
    registry.register(GitTool())
    registry.register(ShellTool())
    return registry


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self, tool_registry):
        """Test registering a tool."""
        tools = tool_registry.list_tools()
        assert len(tools) == 3
        tool_names = [t["name"] for t in tools]
        assert "filesystem" in tool_names
        assert "git" in tool_names
        assert "shell" in tool_names

    def test_get_tool(self, tool_registry):
        """Test getting a tool by name."""
        tool = tool_registry.get("filesystem")
        assert tool is not None
        assert tool.name == "filesystem"

    def test_get_nonexistent_tool(self, tool_registry):
        """Test getting a nonexistent tool."""
        tool = tool_registry.get("nonexistent")
        assert tool is None

    def test_unregister_tool(self, tool_registry):
        """Test unregistering a tool."""
        tool_registry.unregister("shell")
        tool = tool_registry.get("shell")
        assert tool is None

    @pytest.mark.asyncio
    async def test_execute_tool(self, tool_registry):
        """Test executing a tool."""
        result = await tool_registry.execute("shell", {"command": "echo test"})
        assert result.success is True
        assert "test" in result.output["stdout"]


class TestFilesystemTool:
    """Tests for FilesystemTool."""

    @pytest.fixture
    def filesystem_tool(self):
        """Create a filesystem tool."""
        return FilesystemTool()

    @pytest.mark.asyncio
    async def test_write_and_read_file(self, filesystem_tool, temp_dir):
        """Test writing and reading a file."""
        file_path = str(Path(temp_dir) / "test.txt")

        # Write file
        write_result = await filesystem_tool.execute({
            "operation": "write",
            "path": file_path,
            "content": "Hello, World!",
        })
        assert write_result.success is True

        # Read file
        read_result = await filesystem_tool.execute({
            "operation": "read",
            "path": file_path,
        })
        assert read_result.success is True
        assert read_result.output["content"] == "Hello, World!"

    @pytest.mark.asyncio
    async def test_list_directory(self, filesystem_tool, temp_dir):
        """Test listing a directory."""
        # Create some files
        (Path(temp_dir) / "file1.txt").write_text("content1")
        (Path(temp_dir) / "file2.txt").write_text("content2")

        result = await filesystem_tool.execute({
            "operation": "list",
            "path": temp_dir,
        })
        assert result.success is True
        assert result.output["count"] == 2

    @pytest.mark.asyncio
    async def test_check_exists(self, filesystem_tool, temp_dir):
        """Test checking if a path exists."""
        file_path = str(Path(temp_dir) / "exists.txt")

        # File doesn't exist
        result = await filesystem_tool.execute({
            "operation": "exists",
            "path": file_path,
        })
        assert result.success is True
        assert result.output["exists"] is False

        # Create file
        Path(file_path).write_text("content")

        # File exists
        result = await filesystem_tool.execute({
            "operation": "exists",
            "path": file_path,
        })
        assert result.success is True
        assert result.output["exists"] is True

    @pytest.mark.asyncio
    async def test_path_allowed(self, temp_dir):
        """Test path allowed check."""
        tool = FilesystemTool(allowed_paths=[temp_dir])

        # Allowed path
        result = await tool.execute({
            "operation": "exists",
            "path": str(Path(temp_dir) / "test.txt"),
        })
        assert result.success is True

        # Disallowed path
        result = await tool.execute({
            "operation": "exists",
            "path": "/etc/passwd",
        })
        assert result.success is False
        assert "not allowed" in result.error


class TestShellTool:
    """Tests for ShellTool."""

    @pytest.fixture
    def shell_tool(self):
        """Create a shell tool."""
        return ShellTool()

    @pytest.mark.asyncio
    async def test_execute_simple_command(self, shell_tool):
        """Test executing a simple command."""
        result = await shell_tool.execute({"command": "echo hello"})
        assert result.success is True
        assert "hello" in result.output["stdout"]

    @pytest.mark.asyncio
    async def test_execute_command_with_error(self, shell_tool):
        """Test executing a command that fails."""
        result = await shell_tool.execute({"command": "nonexistent_command_12345"})
        assert result.success is False
        assert result.output["returncode"] != 0

    @pytest.mark.asyncio
    async def test_blocked_command(self, shell_tool):
        """Test that dangerous commands are blocked."""
        result = await shell_tool.execute({"command": "rm -rf /"})
        assert result.success is False
        assert "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_sudo_blocked(self, shell_tool):
        """Test that sudo commands are blocked."""
        result = await shell_tool.execute({"command": "sudo ls"})
        assert result.success is False
        assert "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test command timeout."""
        tool = ShellTool(timeout=1)
        result = await tool.execute({"command": "sleep 5"})
        assert result.success is False
        assert "timed out" in result.error.lower()


class TestGitTool:
    """Tests for GitTool."""

    @pytest.fixture
    def git_tool(self):
        """Create a git tool."""
        return GitTool()

    @pytest.mark.asyncio
    async def test_git_status(self, git_tool, temp_dir):
        """Test git status command."""
        # Initialize a git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)

        result = await git_tool.execute({
            "command": "status",
            "cwd": temp_dir,
        })
        assert result.success is True
        assert "On branch" in result.output["stdout"] or "No commits yet" in result.output["stdout"]

    @pytest.mark.asyncio
    async def test_git_version(self, git_tool):
        """Test git version command."""
        result = await git_tool.execute({"command": "version"})
        assert result.success is True
        assert "git version" in result.output["stdout"]

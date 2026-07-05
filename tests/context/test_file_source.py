"""Tests for file context source."""

import tempfile
from pathlib import Path

import pytest
from context import FileContextSource

from contracts import ContextQuery, ProjectRef


@pytest.fixture
def temp_project():
    """Create temporary project with files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        (project_dir / "main.py").write_text("def hello():\n    print('Hello')\n")
        (project_dir / "README.md").write_text("# Test Project\n\nThis is a test.\n")
        (project_dir / ".hidden").write_text("hidden file\n")

        yield str(project_dir)


@pytest.mark.asyncio
async def test_file_source_index(temp_project):
    """Test indexing a project."""
    source = FileContextSource()
    project = ProjectRef(id="test-1", name="Test", path=temp_project)

    result = await source.index(project)
    assert result.project_id == "test-1"
    assert result.status == "indexed"


@pytest.mark.asyncio
async def test_file_source_gather(temp_project):
    """Test gathering context from files."""
    source = FileContextSource()
    project = ProjectRef(id="test-1", name="Test", path=temp_project)
    await source.index(project)

    query = ContextQuery(project_id="test-1", query="test", max_tokens=1000)
    result = await source.gather(query)

    assert len(result.chunks) > 0
    assert result.total_tokens > 0
    assert result.query_time_ms >= 0


@pytest.mark.asyncio
async def test_file_source_skips_hidden(temp_project):
    """Test that hidden files are skipped."""
    source = FileContextSource()
    project = ProjectRef(id="test-1", name="Test", path=temp_project)
    await source.index(project)

    query = ContextQuery(project_id="test-1", query="test", max_tokens=1000)
    result = await source.gather(query)

    file_paths = [chunk.file_path for chunk in result.chunks]
    assert not any(".hidden" in fp for fp in file_paths)

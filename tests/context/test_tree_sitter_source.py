"""Tests for tree-sitter source."""

import tempfile
from pathlib import Path

import pytest
from context import TreeSitterSource

from contracts import ContextQuery, ProjectRef


@pytest.fixture
def temp_python_project():
    """Create temporary Python project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        code = '''
def hello():
    """Say hello."""
    print("Hello")

def goodbye():
    """Say goodbye."""
    print("Goodbye")

class MyClass:
    """A test class."""

    def method(self):
        return 42
'''
        (project_dir / "main.py").write_text(code)

        yield str(project_dir)


@pytest.mark.asyncio
async def test_tree_sitter_parse(temp_python_project):
    """Test parsing Python code."""
    source = TreeSitterSource()
    project = ProjectRef(id="test-1", name="Test", path=temp_python_project)
    await source.index(project)

    query = ContextQuery(project_id="test-1", query="test", max_tokens=1000)
    result = await source.gather(query)

    assert len(result.chunks) > 0
    assert all(chunk.source == "tree-sitter" for chunk in result.chunks)


@pytest.mark.asyncio
async def test_tree_sitter_extracts_functions(temp_python_project):
    """Test that tree-sitter extracts functions."""
    source = TreeSitterSource()
    project = ProjectRef(id="test-1", name="Test", path=temp_python_project)
    await source.index(project)

    query = ContextQuery(project_id="test-1", query="test", max_tokens=1000)
    result = await source.gather(query)

    contents = [chunk.content for chunk in result.chunks]
    assert any("def hello" in c for c in contents)
    assert any("def goodbye" in c for c in contents)

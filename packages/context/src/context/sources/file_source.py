"""File-based context source."""

import os
from pathlib import Path

import aiofiles

from context.token_budget import TokenBudget
from contracts import ContextChunk, ContextQuery, ContextResult, IndexResult, ProjectRef


class FileContextSource:
    """Context source that reads files from a project directory."""

    def __init__(self):
        self.name = "file"
        self._projects: dict[str, str] = {}

    async def gather(self, query: ContextQuery) -> ContextResult:
        """Gather context from files in project."""
        project_path = self._projects.get(query.project_id)
        if not project_path:
            return ContextResult(chunks=[], total_tokens=0, query_time_ms=0.0)

        import time

        start_time = time.time()

        chunks = []
        budget = TokenBudget(query.max_tokens)

        for root, _, files in os.walk(project_path):
            for filename in files:
                if filename.startswith(".") or filename.startswith("_"):
                    continue

                file_path = Path(root) / filename
                rel_path = file_path.relative_to(project_path)

                if not self._is_relevant_file(filename):
                    continue

                try:
                    async with aiofiles.open(file_path, encoding="utf-8") as f:
                        content = await f.read()

                    if budget.can_fit(content):
                        tokens = budget.allocate(content)
                        chunks.append(
                            ContextChunk(
                                id=str(rel_path),
                                content=content,
                                source="file",
                                file_path=str(rel_path),
                                score=1.0,
                                metadata={"tokens": tokens},
                            )
                        )

                    if budget.remaining() <= 0:
                        break

                except Exception:
                    continue

            if budget.remaining() <= 0:
                break

        query_time_ms = (time.time() - start_time) * 1000

        return ContextResult(
            chunks=chunks,
            total_tokens=budget.used_tokens,
            query_time_ms=query_time_ms,
        )

    async def index(self, project: ProjectRef) -> IndexResult:
        """Index a project (no-op for file source)."""
        self._projects[project.id] = project.path
        return IndexResult(
            project_id=project.id,
            chunks_indexed=0,
            index_time_ms=0.0,
            status="indexed",
        )

    async def search(self, query: str, top_k: int = 5) -> list[ContextChunk]:
        """Search for files (returns all files for file source)."""
        return []

    def _is_relevant_file(self, filename: str) -> bool:
        """Check if file is relevant for context."""
        relevant_extensions = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".md",
            ".txt",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".rs",
            ".go",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
        }
        ext = Path(filename).suffix.lower()
        return ext in relevant_extensions

"""Tree-sitter based context source for code parsing."""

import os
from pathlib import Path

import aiofiles
from tree_sitter import Language, Parser

from context.embeddings import EmbeddingPipeline
from context.token_budget import TokenBudget
from contracts import ContextChunk, ContextQuery, ContextResult, IndexResult, ProjectRef

try:
    import tree_sitter_python as tspython
    import tree_sitter_typescript as tstypescript

    PYTHON_LANGUAGE = Language(tspython.language())
    TYPESCRIPT_LANGUAGE = Language(tstypescript.language_typescript())
except ImportError:
    PYTHON_LANGUAGE = None
    TYPESCRIPT_LANGUAGE = None


class TreeSitterSource:
    """Context source that uses tree-sitter to parse code."""

    def __init__(self, embedding_pipeline: EmbeddingPipeline | None = None):
        self.name = "tree-sitter"
        self._projects: dict[str, str] = {}
        self._embedding_pipeline = embedding_pipeline

    async def gather(self, query: ContextQuery) -> ContextResult:
        """Gather context by parsing code files."""
        project_path = self._projects.get(query.project_id)
        if not project_path:
            return ContextResult(chunks=[], total_tokens=0, query_time_ms=0.0)

        import time

        start_time = time.time()

        chunks = []
        budget = TokenBudget(query.max_tokens)

        for root, _, files in os.walk(project_path):
            for filename in files:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(project_path)

                language = self._get_language(filename)
                if not language:
                    continue

                try:
                    async with aiofiles.open(file_path, encoding="utf-8") as f:
                        content = await f.read()

                    parsed_chunks = self._parse_code(content, str(rel_path), language)

                    for chunk in parsed_chunks:
                        if budget.can_fit(chunk.content):
                            tokens = budget.allocate(chunk.content)
                            chunk.metadata["tokens"] = tokens
                            chunks.append(chunk)

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
        """Index a project by parsing code and storing chunks with embeddings."""
        import time

        self._projects[project.id] = project.path
        start_time = time.time()

        chunks = []
        for root, _, files in os.walk(project.path):
            for filename in files:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(project.path)

                language = self._get_language(filename)
                if not language:
                    continue

                try:
                    async with aiofiles.open(file_path, encoding="utf-8") as f:
                        content = await f.read()

                    parsed_chunks = self._parse_code(content, str(rel_path), language)
                    chunks.extend(parsed_chunks)
                except Exception:
                    continue

        if self._embedding_pipeline and chunks:
            await self._embedding_pipeline.store_chunks(chunks, project.id)

        index_time_ms = (time.time() - start_time) * 1000

        return IndexResult(
            project_id=project.id,
            chunks_indexed=len(chunks),
            index_time_ms=index_time_ms,
            status="indexed",
        )

    async def search(self, query: str, project_id: str, top_k: int = 5) -> list[ContextChunk]:
        """Search for relevant code using embeddings."""
        if not self._embedding_pipeline:
            return []

        return await self._embedding_pipeline.search(query, project_id, top_k)

    def _get_language(self, filename: str) -> Language | None:
        """Get tree-sitter language for file."""
        ext = Path(filename).suffix.lower()
        if ext == ".py" and PYTHON_LANGUAGE:
            return PYTHON_LANGUAGE
        if ext in {".ts", ".tsx"} and TYPESCRIPT_LANGUAGE:
            return TYPESCRIPT_LANGUAGE
        return None

    def _parse_code(self, content: str, file_path: str, language: Language) -> list[ContextChunk]:
        """Parse code and extract functions/classes."""
        parser = Parser(language)
        tree = parser.parse(content.encode())

        chunks = []
        root_node = tree.root_node

        for child in root_node.children:
            if child.type in {
                "function_definition",
                "class_definition",
                "function_declaration",
                "class_declaration",
            }:
                chunk_content = content[child.start_byte : child.end_byte]
                chunks.append(
                    ContextChunk(
                        id=f"{file_path}:{child.start_point[0]}",
                        content=chunk_content,
                        source="tree-sitter",
                        file_path=file_path,
                        line_start=child.start_point[0],
                        line_end=child.end_point[0],
                        score=1.0,
                        metadata={"type": child.type},
                    )
                )

        return chunks

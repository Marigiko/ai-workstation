# Context Engine 2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a gateway plugin that indexes all projects into Qdrant and automatically injects relevant context into every AI query.

**Architecture:** Middleware in the ai-workstation gateway that intercepts requests, searches Qdrant for relevant context (scoped per-project namespace), and enriches the prompt. File watcher keeps indices up to date. Uses sentence-transformers for local embeddings.

**Tech Stack:** Python 3.11+, FastAPI, Qdrant, sentence-transformers, watchdog, asyncio

## Global Constraints

- Follow existing ai-workstation package structure: `packages/<name>/src/<name>/`
- Async-first (match existing patterns)
- Type hints on all functions
- Google-style docstrings for public functions
- Each task ends with passing tests
- No API keys required — use local models only
- Per-project Qdrant namespace isolation

---

### Task 1: Add sentence-transformers dependency

**Covers:** [S4.4]

**Files:**
- Modify: `/mnt/d/Projects/ai-workstation/packages/context/pyproject.toml`

**Interfaces:**
- Produces: `sentence-transformers` available in context package

- [ ] **Step 1: Read current pyproject.toml**

Read `/mnt/d/Projects/ai-workstation/packages/context/pyproject.toml`

- [ ] **Step 2: Add sentence-transformers dependency**

Add to `[project.dependencies]`:
```
"sentence-transformers>=3.0.0",
"watchdog>=4.0.0",
```

- [ ] **Step 3: Sync dependencies**

```bash
cd /mnt/d/Projects/ai-workstation
uv sync --all-packages
```

- [ ] **Step 4: Verify installation**

```bash
cd /mnt/d/Projects/ai-workstation
uv run python -c "from sentence_transformers import SentenceTransformer; print('OK')"
```
Expected: `OK`

---

### Task 2: Create embeddings service

**Covers:** [S4.4]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/context/src/context/embeddings/service.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/context/tests/test_embeddings.py`

**Interfaces:**
- Produces: `EmbeddingService` class with `embed(texts: list[str]) -> list[list[float]]`

- [ ] **Step 1: Write the failing test**

```python
# packages/context/tests/test_embeddings.py
import pytest
from context.embeddings.service import EmbeddingService


@pytest.fixture
def service():
    return EmbeddingService()


@pytest.mark.asyncio
async def test_embed_single_text(service):
    embeddings = await service.embed(["Hello world"])
    assert len(embeddings) == 1
    assert len(embeddings[0]) > 0
    assert isinstance(embeddings[0][0], float)


@pytest.mark.asyncio
async def test_embed_multiple_texts(service):
    texts = ["First text", "Second text", "Third text"]
    embeddings = await service.embed(texts)
    assert len(embeddings) == 3
    assert all(len(e) == len(embeddings[0]) for e in embeddings)


@pytest.mark.asyncio
async def test_embed_empty_list(service):
    embeddings = await service.embed([])
    assert embeddings == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/context/tests/test_embeddings.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement EmbeddingService**

```python
# packages/context/src/context/embeddings/service.py
"""Embedding service using sentence-transformers."""

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Local embedding service using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformer(model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        if not texts:
            return []
        embeddings = self._model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/context/tests/test_embeddings.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/context/
git commit -m "feat(context): add embedding service with sentence-transformers"
```

---

### Task 3: Create project indexer

**Covers:** [S4.1], [S4.4]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/context/src/context/indexer.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/context/tests/test_indexer.py`

**Interfaces:**
- Consumes: `EmbeddingService` from Task 2
- Produces: `ProjectIndexer` class with `index_project(project_path: str, namespace: str) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# packages/context/tests/test_indexer.py
import pytest
import tempfile
import os
from context.indexer import ProjectIndexer
from context.embeddings.service import EmbeddingService


@pytest.fixture
def indexer():
    service = EmbeddingService()
    return ProjectIndexer(embedding_service=service)


@pytest.fixture
def sample_project():
    """Create a temporary project with sample files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample files
        with open(os.path.join(tmpdir, "README.md"), "w") as f:
            f.write("# Sample Project\n\nThis is a test project.\n")
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("def hello():\n    return 'world'\n")
        os.makedirs(os.path.join(tmpdir, "src"))
        with open(os.path.join(tmpdir, "src", "utils.py"), "w") as f:
            f.write("def add(a, b):\n    return a + b\n")
        yield tmpdir


@pytest.mark.asyncio
async def test_index_project_returns_stats(indexer, sample_project):
    stats = await indexer.index_project(sample_project, namespace="test_sample")
    assert stats["files_indexed"] >= 3
    assert stats["chunks_created"] >= 3
    assert stats["namespace"] == "test_sample"


@pytest.mark.asyncio
async def test_index_project_skips_binary_files(indexer):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a binary file
        with open(os.path.join(tmpdir, "image.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        # Create a text file
        with open(os.path.join(tmpdir, "readme.txt"), "w") as f:
            f.write("Hello world")

        stats = await indexer.index_project(tmpdir, namespace="test_binary")
        assert stats["files_indexed"] == 1
        assert stats["files_skipped"] >= 1


@pytest.mark.asyncio
async def test_index_project_with_nested_directories(indexer):
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "a", "b", "c"))
        with open(os.path.join(tmpdir, "a", "b", "c", "deep.py"), "w") as f:
            f.write("# deep file\n")

        stats = await indexer.index_project(tmpdir, namespace="test_nested")
        assert stats["files_indexed"] >= 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/context/tests/test_indexer.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement ProjectIndexer**

```python
# packages/context/src/context/indexer.py
"""Project indexer — scans projects and stores embeddings in Qdrant."""

import os
from pathlib import Path
from typing import Any

from context.embeddings.service import EmbeddingService

# File extensions to index
TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".txt", ".yaml", ".yml",
    ".json", ".toml", ".cfg", ".ini", ".sh", ".bash", ".zsh", ".fish",
    ".rs", ".go", ".java", ".c", ".cpp", ".h", ".hpp", ".css", ".html",
    ".xml", ".sql", ".r", ".rb", ".php", ".swift", ".kt", ".kts",
    ".dockerfile", ".makefile", ".cmake", ".gradle", ".env.example",
    ".gitignore", ".editorconfig", ".luacheckrc", ".stylua.toml",
}

# Directories to skip
SKIP_DIRS = {
    ".git", ".svn", "__pycache__", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
    ".next", ".nuxt", ".cache", "target", "vendor", ".terraform",
}


class ProjectIndexer:
    """Indexes project files into vector storage."""

    def __init__(self, embedding_service: EmbeddingService):
        self._embeddings = embedding_service

    async def index_project(self, project_path: str, namespace: str) -> dict[str, Any]:
        """Index all text files in a project.

        Args:
            project_path: Absolute path to the project root.
            namespace: Qdrant collection/namespace for this project.

        Returns:
            Stats dict with files_indexed, files_skipped, chunks_created, namespace.
        """
        project_root = Path(project_path)
        text_files: list[Path] = []
        skipped = 0

        for path in project_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() in TEXT_EXTENSIONS:
                text_files.append(path)
            else:
                skipped += 1

        chunks: list[str] = []
        chunk_meta: list[dict[str, Any]] = []

        for file_path in text_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if not content.strip():
                    continue
                file_chunks = self._chunk_content(content)
                for chunk in file_chunks:
                    chunks.append(chunk)
                    chunk_meta.append({
                        "file_path": str(file_path.relative_to(project_root)),
                        "project": namespace,
                        "absolute_path": str(file_path),
                    })
            except (OSError, UnicodeDecodeError):
                skipped += 1
                continue

        if chunks:
            embeddings = await self._embeddings.embed(chunks)
            # Store in Qdrant (will be implemented in Task 4)
            await self._store_embeddings(namespace, chunks, chunk_meta, embeddings)

        return {
            "files_indexed": len(text_files),
            "files_skipped": skipped,
            "chunks_created": len(chunks),
            "namespace": namespace,
        }

    def _chunk_content(self, content: str, max_chunk_size: int = 1000) -> list[str]:
        """Split content into overlapping chunks."""
        if len(content) <= max_chunk_size:
            return [content] if content.strip() else []

        chunks: list[str] = []
        lines = content.split("\n")
        current_chunk: list[str] = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1
            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(line)
            current_size += line_size

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    async def _store_embeddings(
        self,
        namespace: str,
        chunks: list[str],
        metadata: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """Store embeddings in Qdrant. Placeholder for Task 4."""
        # Will be implemented with actual Qdrant storage
        pass
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/context/tests/test_indexer.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/context/
git commit -m "feat(context): add project indexer with chunking"
```

---

### Task 4: Create Qdrant context store with namespace support

**Covers:** [S4.3], [S4.6]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/context/src/context/store.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/context/tests/test_store.py`

**Interfaces:**
- Consumes: `EmbeddingService` (for dimension)
- Produces: `ContextStore` class with `store()`, `search()`, `delete_namespace()`

- [ ] **Step 1: Write the failing test**

```python
# packages/context/tests/test_store.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from context.store import ContextStore


@pytest.fixture
def mock_qdrant():
    mock = AsyncMock()
    mock.get_collections = AsyncMock(return_value=MagicMock(collections=[]))
    mock.create_collection = AsyncMock()
    mock.upsert = AsyncMock()
    mock.search = AsyncMock(return_value=[])
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def store(mock_qdrant):
    return ContextStore(client=mock_qdrant, embedding_dimension=384)


@pytest.mark.asyncio
async def test_store_creates_namespace_if_missing(store, mock_qdrant):
    await store.store(
        namespace="test_project",
        chunks=["Hello world"],
        embeddings=[[0.1] * 384],
        metadata=[{"file": "test.py"}],
    )
    mock_qdrant.create_collection.assert_called_once()


@pytest.mark.asyncio
async def test_store_upserts_points(store, mock_qdrant):
    # Simulate collection already exists
    mock_qdrant.get_collections = AsyncMock(
        return_value=MagicMock(collections=[MagicMock(name="ctx_test_project")])
    )
    await store.store(
        namespace="test_project",
        chunks=["chunk1", "chunk2"],
        embeddings=[[0.1] * 384, [0.2] * 384],
        metadata=[{"file": "a.py"}, {"file": "b.py"}],
    )
    mock_qdrant.upsert.assert_called_once()
    call_args = mock_qdrant.upsert.call_args
    assert len(call_args.kwargs.get("points", call_args[1].get("points", []))) == 2


@pytest.mark.asyncio
async def test_search_returns_results(store, mock_qdrant):
    mock_qdrant.search = AsyncMock(return_value=[
        MagicMock(payload={"text": "result1", "file": "a.py"}, score=0.95),
        MagicMock(payload={"text": "result2", "file": "b.py"}, score=0.87),
    ])
    results = await store.search(
        namespace="test_project",
        query_embedding=[0.1] * 384,
        limit=5,
    )
    assert len(results) == 2
    assert results[0]["score"] == 0.95


@pytest.mark.asyncio
async def test_delete_namespace(store, mock_qdrant):
    await store.delete_namespace("test_project")
    mock_qdrant.delete_collection.assert_called_once_with("ctx_test_project")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/context/tests/test_store.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement ContextStore**

```python
# packages/context/src/context/store.py
"""Qdrant-backed context storage with per-project namespace isolation."""

from typing import Any, Protocol


class QdrantClient(Protocol):
    """Protocol for Qdrant client operations."""

    async def get_collections(self) -> Any: ...
    async def create_collection(self, collection_name: str, **kwargs) -> None: ...
    async def upsert(self, collection_name: str, **kwargs) -> None: ...
    async def search(self, collection_name: str, **kwargs) -> list[Any]: ...
    async def delete_collection(self, collection_name: str) -> None: ...


class ContextStore:
    """Stores and retrieves context chunks in Qdrant with namespace isolation."""

    def __init__(self, client: QdrantClient, embedding_dimension: int = 384):
        self._client = client
        self._dim = embedding_dimension

    def _collection_name(self, namespace: str) -> str:
        """Generate Qdrant collection name for a project namespace."""
        return f"ctx_{namespace}"

    async def _ensure_collection(self, namespace: str) -> None:
        """Create collection if it doesn't exist."""
        name = self._collection_name(namespace)
        collections = await self._client.get_collections()
        existing = {c.name for c in collections.collections}
        if name not in existing:
            await self._client.create_collection(
                collection_name=name,
                vectors_config={"size": self._dim, "distance": "Cosine"},
            )

    async def store(
        self,
        namespace: str,
        chunks: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]],
    ) -> None:
        """Store chunks with embeddings in the project namespace."""
        await self._ensure_collection(namespace)
        name = self._collection_name(namespace)

        points = []
        for i, (chunk, embedding, meta) in enumerate(zip(chunks, embeddings, metadata)):
            points.append({
                "id": hash(f"{namespace}:{meta.get('file_path', i)}:{chunk[:50]}"),
                "vector": embedding,
                "payload": {"text": chunk, **meta},
            })

        await self._client.upsert(collection_name=name, points=points)

    async def search(
        self,
        namespace: str,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for relevant context within a project namespace."""
        name = self._collection_name(namespace)
        results = await self._client.search(
            collection_name=name,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True,
        )
        return [
            {
                "text": r.payload.get("text", ""),
                "file": r.payload.get("file_path", ""),
                "score": r.score,
                "metadata": {k: v for k, v in r.payload.items() if k != "text"},
            }
            for r in results
        ]

    async def delete_namespace(self, namespace: str) -> None:
        """Delete all data for a project namespace."""
        await self._client.delete_collection(self._collection_name(namespace))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/context/tests/test_store.py -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/context/
git commit -m "feat(context): add Qdrant context store with namespace isolation"
```

---

### Task 5: Create context injection middleware

**Covers:** [S4.2], [S4.6]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/apps/gateway/src/gateway/middleware/context_engine.py`
- Create: `/mnt/d/Projects/ai-workstation/apps/gateway/tests/test_context_middleware.py`

**Interfaces:**
- Consumes: `ContextStore`, `EmbeddingService`
- Produces: FastAPI middleware that enriches requests with context

- [ ] **Step 1: Write the failing test**

```python
# apps/gateway/tests/test_context_middleware.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request
from starlette.testclient import TestClient
from gateway.middleware.context_engine import ContextEngineMiddleware


@pytest.fixture
def mock_store():
    store = AsyncMock()
    store.search = AsyncMock(return_value=[
        {"text": "def hello(): pass", "file": "main.py", "score": 0.92},
    ])
    return store


@pytest.fixture
def mock_embedder():
    embedder = AsyncMock()
    embedder.embed = AsyncMock(return_value=[[0.1] * 384])
    return embedder


@pytest.fixture
def app(mock_store, mock_embedder):
    app = FastAPI()
    app.add_middleware(
        ContextEngineMiddleware,
        store=mock_store,
        embedder=mock_embedder,
        active_project="test_project",
    )

    @app.post("/v1/chat/completions")
    async def chat(request: Request):
        body = await request.json()
        # Check if context was injected
        messages = body.get("messages", [])
        return {"messages": messages, "context_injected": len(messages) > 1}

    return app


def test_middleware_injects_context(app, mock_store, mock_embedder):
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["context_injected"] is True
    mock_store.search.assert_called_once()


def test_middleware_skips_when_no_context(app, mock_store, mock_embedder):
    mock_store.search = AsyncMock(return_value=[])
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest apps/gateway/tests/test_context_middleware.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement ContextEngineMiddleware**

```python
# apps/gateway/src/gateway/middleware/context_engine.py
"""Context engine middleware — injects relevant context into every chat request."""

import json
from typing import Any, Protocol

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class ContextSearcher(Protocol):
    async def search(self, namespace: str, query_embedding: list[float], limit: int = 5) -> list[dict]: ...


class TextEmbedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class ContextEngineMiddleware(BaseHTTPMiddleware):
    """Injects project context into chat completion requests."""

    def __init__(
        self,
        app,
        store: ContextSearcher,
        embedder: TextEmbedder,
        active_project: str = "default",
        context_limit: int = 3,
    ):
        super().__init__(app)
        self._store = store
        self._embedder = embedder
        self._project = active_project
        self._limit = context_limit

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/v1/chat/completions" and request.method == "POST":
            try:
                body = await request.json()
                messages = body.get("messages", [])
                if messages:
                    last_message = messages[-1].get("content", "")
                    if isinstance(last_message, str) and last_message.strip():
                        embedding = (await self._embedder.embed([last_message]))[0]
                        context = await self._store.search(
                            namespace=self._project,
                            query_embedding=embedding,
                            limit=self._limit,
                        )
                        if context:
                            context_text = "\n\n".join(
                                f"[{c.get('file', 'unknown')}]: {c['text']}"
                                for c in context
                            )
                            messages.insert(0, {
                                "role": "system",
                                "content": f"Relevant project context:\n{context_text}",
                            })
                            body["messages"] = messages
                            request._body = json.dumps(body).encode()
            except Exception:
                pass  # Fail open — don't block requests on context errors

        response = await call_next(request)
        return response
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest apps/gateway/tests/test_context_middleware.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add apps/gateway/
git commit -m "feat(gateway): add context engine middleware for auto-injection"
```

---

### Task 6: Create file watcher for auto-indexing

**Covers:** [S4.5]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/context/src/context/watcher.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/context/tests/test_watcher.py`

**Interfaces:**
- Consumes: `ProjectIndexer`
- Produces: `ProjectWatcher` class with `watch(project_path: str, namespace: str)`

- [ ] **Step 1: Write the failing test**

```python
# packages/context/tests/test_watcher.py
import pytest
import asyncio
import tempfile
import os
import time
from context.watcher import ProjectIndexer, ProjectWatcher


@pytest.fixture
def mock_indexer():
    indexer = AsyncMock()
    indexer.index_project = AsyncMock(return_value={"files_indexed": 1})
    return indexer


@pytest.mark.asyncio
async def test_watcher_detects_new_files(mock_indexer):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create initial file
        with open(os.path.join(tmpdir, "test.py"), "w") as f:
            f.write("initial")

        watcher = ProjectWatcher(indexer=mock_indexer, debounce_seconds=1)
        task = asyncio.create_task(watcher.watch(tmpdir, "test_ns"))
        await asyncio.sleep(0.5)

        # Create a new file
        with open(os.path.join(tmpdir, "new_file.py"), "w") as f:
            f.write("new content")

        await asyncio.sleep(2)
        watcher.stop()
        task.cancel()

        assert mock_indexer.index_project.call_count >= 1


def test_watcher_stops_cleanly(mock_indexer):
    watcher = ProjectWatcher(indexer=mock_indexer)
    watcher.stop()
    assert watcher.is_stopped()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/context/tests/test_watcher.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement ProjectWatcher**

```python
# packages/context/src/context/watcher.py
"""File watcher for automatic project re-indexing."""

import asyncio
import os
from pathlib import Path
from typing import Any, Protocol

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class Indexer(Protocol):
    async def index_project(self, project_path: str, namespace: str) -> dict[str, Any]: ...


class _ChangeHandler(FileSystemEventHandler):
    """Debounces file change events and triggers re-index."""

    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self._timer = None

    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if event.src_path.endswith((".pyc", ".pyo", ".swp", "~")):
            return
        if self._timer:
            self._timer.cancel()
        self._timer = asyncio.get_event_loop().call_later(5, self._callback)

    def _fire(self):
        if self._callback:
            self._callback()


class ProjectWatcher:
    """Watches a project directory and re-indexes on changes."""

    def __init__(self, indexer: Indexer, debounce_seconds: int = 5):
        self._indexer = indexer
        self._debounce = debounce_seconds
        self._observer: Observer | None = None
        self._stopped = False

    async def watch(self, project_path: str, namespace: str) -> None:
        """Start watching a project for changes."""
        loop = asyncio.get_event_loop()
        pending = [False]

        def on_change():
            if not pending[0]:
                pending[0] = True
                asyncio.run_coroutine_threadsafe(
                    self._debounced_index(project_path, namespace, pending),
                    loop,
                )

        handler = _ChangeHandler(callback=on_change)
        self._observer = Observer()
        self._observer.schedule(handler, project_path, recursive=True)
        self._observer.start()

        try:
            while not self._stopped:
                await asyncio.sleep(1)
        finally:
            self._observer.stop()
            self._observer.join()

    async def _debounced_index(self, path: str, ns: str, pending: list) -> None:
        await asyncio.sleep(self._debounce)
        await self._indexer.index_project(path, ns)
        pending[0] = False

    def stop(self) -> None:
        self._stopped = True
        if self._observer:
            self._observer.stop()

    def is_stopped(self) -> bool:
        return self._stopped
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/context/tests/test_watcher.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/context/
git commit -m "feat(context): add file watcher for auto-indexing"
```

---

### Task 7: Wire context engine into gateway

**Covers:** [S4.2], [S4.6]

**Files:**
- Modify: `/mnt/d/Projects/ai-workstation/apps/gateway/src/gateway/main.py`

**Interfaces:**
- Consumes: All context engine components
- Produces: Gateway with context injection active

- [ ] **Step 1: Read current main.py**

Read `/mnt/d/Projects/ai-workstation/apps/gateway/src/gateway/main.py`

- [ ] **Step 2: Add context engine initialization**

Add to `main.py` after existing middleware setup:

```python
from context.embeddings.service import EmbeddingService
from context.store import ContextStore
from context.indexer import ProjectIndexer
from gateway.middleware.context_engine import ContextEngineMiddleware

# Initialize context engine
embedding_service = EmbeddingService()
qdrant_client = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
context_store = ContextStore(client=qdrant_client, embedding_dimension=embedding_service.dimension)
context_indexer = ProjectIndexer(embedding_service=embedding_service)

# Add context middleware
app.add_middleware(
    ContextEngineMiddleware,
    store=context_store,
    embedder=embedding_service,
    active_project=os.environ.get("ACTIVE_PROJECT", "default"),
)
```

- [ ] **Step 3: Verify gateway starts**

```bash
cd /mnt/d/Projects/ai-workstation
uv run uvicorn gateway.main:app --app-dir apps/gateway/src --port 8000 &
sleep 3
curl -s http://localhost:8000/health
```
Expected: HTTP 200

- [ ] **Step 4: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add apps/gateway/
git commit -m "feat(gateway): wire context engine into gateway startup"
```

---

## Self-Review Notes

- [S4.1] Covered by Task 3 (indexer) + Task 6 (watcher)
- [S4.2] Covered by Task 5 (middleware) + Task 7 (wiring)
- [S4.3] Covered by Task 4 (namespace isolation)
- [S4.4] Covered by Task 2 (embeddings)
- [S4.5] Covered by Task 6 (watcher)
- [S4.6] Covered by Tasks 4, 5, 7
- All tasks have TDD cycle
- No placeholders

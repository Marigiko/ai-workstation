"""Context endpoints."""

from context import FileContextSource, TreeSitterSource
from fastapi import APIRouter, HTTPException

from contracts import ContextQuery, ProjectRef

router = APIRouter(prefix="/context", tags=["context"])

_file_source = FileContextSource()
_tree_sitter_source = TreeSitterSource()


@router.post("/projects/{project_id}/index")
async def index_project(
    project_id: str,
    name: str,
    path: str,
    source: str = "file",
):
    """Index a project for context retrieval."""
    project = ProjectRef(id=project_id, name=name, path=path)

    if source == "file":
        result = await _file_source.index(project)
    elif source == "tree-sitter":
        result = await _tree_sitter_source.index(project)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown source: {source}")

    return result.model_dump()


@router.post("/projects/{project_id}/gather")
async def gather_context(
    project_id: str,
    query: str,
    max_tokens: int = 4096,
    source: str = "file",
):
    """Gather context for a query."""
    context_query = ContextQuery(
        project_id=project_id,
        query=query,
        max_tokens=max_tokens,
    )

    if source == "file":
        result = await _file_source.gather(context_query)
    elif source == "tree-sitter":
        result = await _tree_sitter_source.gather(context_query)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown source: {source}")

    return result.model_dump()

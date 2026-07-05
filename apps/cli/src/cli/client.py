"""HTTP client for AI Workstation Gateway."""

import os
from typing import Any

import httpx


class GatewayClient:
    """Client for communicating with the AI Workstation Gateway."""

    def __init__(self, base_url: str | None = None):
        """Initialize gateway client.

        Args:
            base_url: Gateway base URL (defaults to GATEWAY_URL env var or http://localhost:8000)
        """
        self.base_url = base_url or os.getenv("GATEWAY_URL", "http://localhost:8000")
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def health_check(self) -> dict[str, Any]:
        """Check gateway health."""
        response = self.client.get("/health")
        response.raise_for_status()
        return response.json()

    # Chat operations
    def chat(
        self,
        messages: list[dict[str, str]],
        session_id: str | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Send chat request."""
        payload = {"messages": messages, "stream": stream}
        params = {"session_id": session_id} if session_id else None
        response = self.client.post("/chat", json=payload, params=params)
        response.raise_for_status()
        return response.json()

    # Session operations
    def create_session(self, title: str | None = None) -> dict[str, Any]:
        """Create a new session."""
        params = {"title": title} if title else None
        response = self.client.post("/sessions", params=params)
        response.raise_for_status()
        return response.json()

    def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        """List sessions."""
        response = self.client.get("/sessions", params={"limit": limit})
        response.raise_for_status()
        return response.json()

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Get session details."""
        response = self.client.get(f"/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    def delete_session(self, session_id: str) -> dict[str, Any]:
        """Delete a session."""
        response = self.client.delete(f"/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    # Context operations
    def index_project(
        self,
        project_id: str,
        name: str,
        path: str,
        source: str = "file",
    ) -> dict[str, Any]:
        """Index a project."""
        params = {"name": name, "path": path, "source": source}
        response = self.client.post(f"/context/projects/{project_id}/index", params=params)
        response.raise_for_status()
        return response.json()

    def gather_context(
        self,
        project_id: str,
        query: str,
        max_tokens: int = 4096,
        source: str = "file",
    ) -> dict[str, Any]:
        """Gather context for a query."""
        params = {"query": query, "max_tokens": max_tokens, "source": source}
        response = self.client.post(f"/context/projects/{project_id}/gather", params=params)
        response.raise_for_status()
        return response.json()

    # Tools operations
    def list_tools(self) -> dict[str, Any]:
        """List available tools."""
        response = self.client.get("/tools")
        response.raise_for_status()
        return response.json()

    def execute_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool."""
        response = self.client.post(f"/tools/{tool_name}/execute", json={"params": params})
        response.raise_for_status()
        return response.json()

    # Skills operations
    def list_skills(self) -> dict[str, Any]:
        """List available skills."""
        response = self.client.get("/skills")
        response.raise_for_status()
        return response.json()

    def execute_skill(
        self,
        skill_name: str,
        variables: dict[str, str],
        context: str | None = None,
    ) -> dict[str, Any]:
        """Execute a skill."""
        payload = {"skill_name": skill_name, "variables": variables}
        if context:
            payload["context"] = context
        response = self.client.post("/skills/execute", json=payload)
        response.raise_for_status()
        return response.json()

    # Memory operations
    def remember(
        self,
        content: str,
        scope: str,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Store a memory."""
        params = {"content": content, "scope": scope}
        if project_id:
            params["project_id"] = project_id
        if session_id:
            params["session_id"] = session_id
        response = self.client.post("/memory/remember", params=params)
        response.raise_for_status()
        return response.json()

    def recall(
        self,
        query: str,
        scope: str,
        limit: int = 10,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Recall memories."""
        params = {"query": query, "scope": scope, "limit": limit}
        if project_id:
            params["project_id"] = project_id
        if session_id:
            params["session_id"] = session_id
        response = self.client.post("/memory/recall", params=params)
        response.raise_for_status()
        return response.json()

    # Evaluation operations
    def evaluate(
        self,
        query: str,
        response: str,
        metrics: list[str] | None = None,
        context: list[str] | None = None,
    ) -> dict[str, Any]:
        """Evaluate a response."""
        payload = {"query": query, "response": response}
        if metrics:
            payload["metrics"] = metrics
        if context:
            payload["context"] = context
        response_http = self.client.post("/evaluation/evaluate", json=payload)
        response_http.raise_for_status()
        return response_http.json()

    # Observability operations
    def get_observability_summary(self) -> dict[str, Any]:
        """Get observability summary."""
        response = self.client.get("/observability/summary")
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the client."""
        self.client.close()

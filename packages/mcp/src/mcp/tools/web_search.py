"""Web search tool using external search APIs."""

import os
from typing import Any

import httpx

from contracts import ToolResult


class WebSearchTool:
    """Tool for searching the web using search APIs.

    Supports multiple backends: SearXNG, Tavily, DuckDuckGo.
    Falls back to a simple DuckDuckGo HTML scrape if no API key is configured.
    """

    name = "web_search"
    description = "Search the web for information. Returns relevant snippets and URLs."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    def __init__(self):
        self.searxng_url = os.getenv("SEARXNG_URL")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute web search."""
        query = params.get("query", "")
        max_results = params.get("max_results", 5)

        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Query is required",
            )

        try:
            if self.tavily_api_key:
                results = await self._search_tavily(query, max_results)
            elif self.searxng_url:
                results = await self._search_searxng(query, max_results)
            else:
                results = await self._search_duckduckgo(query, max_results)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=results,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=str(e),
            )

    async def _search_tavily(self, query: str, max_results: int) -> list[dict]:
        """Search using Tavily API."""
        response = await self._client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self.tavily_api_key,
                "query": query,
                "max_results": max_results,
            },
        )
        response.raise_for_status()
        data = response.json()
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
            for r in data.get("results", [])
        ]

    async def _search_searxng(self, query: str, max_results: int) -> list[dict]:
        """Search using SearXNG instance."""
        response = await self._client.get(
            f"{self.searxng_url}/search",
            params={"q": query, "format": "json", "pageno": 1},
        )
        response.raise_for_status()
        data = response.json()
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
            for r in data.get("results", [])[:max_results]
        ]

    async def _search_duckduckgo(self, query: str, max_results: int) -> list[dict]:
        """Search using DuckDuckGo HTML (fallback)."""
        response = await self._client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()

        import re
        results = []
        link_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>'
        links = re.findall(link_pattern, response.text)
        snippets = re.findall(r'<a class="result__snippet"[^>]*>([^<]+)</a>', response.text)

        for i, (url, title) in enumerate(links[:max_results]):
            snippet = snippets[i] if i < len(snippets) else ""
            results.append({"title": title.strip(), "url": url, "snippet": snippet.strip()})

        return results

    async def close(self):
        await self._client.aclose()

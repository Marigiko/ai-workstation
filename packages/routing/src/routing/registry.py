"""Provider registry for managing multiple LLM providers."""


from contracts import Provider, ProviderCapabilities


class ProviderRegistry:
    """Registry for managing multiple LLM providers."""

    def __init__(self):
        self._providers: dict[str, Provider] = {}
        self._capabilities: dict[str, ProviderCapabilities] = {}

    def register(self, provider: Provider):
        """Register a provider."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> Provider | None:
        """Get a provider by name."""
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    async def get_capabilities(self, name: str) -> ProviderCapabilities | None:
        """Get capabilities for a provider."""
        if name not in self._capabilities:
            provider = self.get(name)
            if provider:
                self._capabilities[name] = await provider.capabilities()
        return self._capabilities.get(name)

    async def get_all_capabilities(self) -> dict[str, ProviderCapabilities]:
        """Get capabilities for all providers."""
        for name in self._providers:
            if name not in self._capabilities:
                provider = self.get(name)
                if provider:
                    self._capabilities[name] = await provider.capabilities()
        return self._capabilities.copy()

    async def health_check(self, name: str) -> bool:
        """Check health of a provider."""
        provider = self.get(name)
        if not provider:
            return False
        return await provider.health()

    async def health_check_all(self) -> dict[str, bool]:
        """Check health of all providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.health()
            except Exception:
                results[name] = False
        return results

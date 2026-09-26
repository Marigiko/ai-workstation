"""Tests that at least one provider is registered (offline registration check)."""

import pytest
from providers import OmniRouteProvider
from routing import ProviderRegistry


@pytest.mark.asyncio
async def test_at_least_one_provider_registered(monkeypatch):
    monkeypatch.setenv("OMNIROUTE_API_KEY", "test-key")
    registry = ProviderRegistry()
    registry.register(OmniRouteProvider(model="liviano"))
    providers = registry.list_providers()
    assert len(providers) >= 1, f"No providers registered. Got: {providers}"

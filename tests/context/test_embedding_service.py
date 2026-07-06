"""Tests for embedding service."""

import pytest
from context.embeddings.service import EmbeddingService


@pytest.mark.asyncio
async def test_embed_single():
    """Test embedding a single text."""
    service = EmbeddingService(api_key=None)
    embedding = await service.embed_single("hello world")

    assert isinstance(embedding, list)
    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_embed_batch():
    """Test embedding multiple texts."""
    service = EmbeddingService(api_key=None)
    texts = ["hello", "world", "test"]
    embeddings = await service.embed(texts)

    assert len(embeddings) == 3
    assert all(len(emb) == 1536 for emb in embeddings)


@pytest.mark.asyncio
async def test_embed_without_api_key():
    """Test embedding without API key returns zero vectors."""
    service = EmbeddingService(api_key=None)
    embedding = await service.embed_single("test")

    assert all(x == 0.0 for x in embedding)


@pytest.mark.asyncio
async def test_custom_dimensions():
    """Test custom embedding dimensions."""
    service = EmbeddingService(api_key=None, dimensions=768)
    embedding = await service.embed_single("test")

    assert len(embedding) == 768

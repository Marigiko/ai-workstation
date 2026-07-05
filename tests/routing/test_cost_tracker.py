"""Tests for cost tracker."""

import pytest
from routing import CostTracker


def test_record_cost():
    """Test recording a cost."""
    tracker = CostTracker()
    tracker.record("openai", "gpt-4", 0.05, 100)

    assert tracker.total_cost() == pytest.approx(0.05)
    assert tracker.total_tokens() == 100


def test_total_cost_multiple():
    """Test total cost with multiple records."""
    tracker = CostTracker()
    tracker.record("openai", "gpt-4", 0.05, 100)
    tracker.record("anthropic", "claude-3", 0.03, 80)

    assert tracker.total_cost() == pytest.approx(0.08)
    assert tracker.total_tokens() == 180


def test_total_cost_by_provider():
    """Test total cost filtered by provider."""
    tracker = CostTracker()
    tracker.record("openai", "gpt-4", 0.05, 100)
    tracker.record("openai", "gpt-3.5", 0.01, 50)
    tracker.record("anthropic", "claude-3", 0.03, 80)

    assert tracker.total_cost("openai") == pytest.approx(0.06)
    assert tracker.total_cost("anthropic") == pytest.approx(0.03)


def test_get_records():
    """Test getting recent records."""
    tracker = CostTracker()
    tracker.record("openai", "gpt-4", 0.05, 100)
    tracker.record("anthropic", "claude-3", 0.03, 80)

    records = tracker.get_records(limit=10)
    assert len(records) == 2


def test_reset():
    """Test resetting tracker."""
    tracker = CostTracker()
    tracker.record("openai", "gpt-4", 0.05, 100)
    tracker.reset()

    assert tracker.total_cost() == 0.0
    assert tracker.total_tokens() == 0

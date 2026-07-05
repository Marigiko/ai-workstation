"""Tests for token budget."""

from context import TokenBudget


def test_token_budget_creation():
    """Test token budget initialization."""
    budget = TokenBudget(max_tokens=1000)
    assert budget.max_tokens == 1000
    assert budget.used_tokens == 0


def test_count_tokens():
    """Test token counting."""
    budget = TokenBudget(max_tokens=1000)
    tokens = budget.count_tokens("Hello world")
    assert tokens > 0


def test_can_fit():
    """Test can_fit check."""
    budget = TokenBudget(max_tokens=10)
    assert budget.can_fit("Hi") is True
    assert budget.can_fit("A" * 1000) is False


def test_allocate():
    """Test token allocation."""
    budget = TokenBudget(max_tokens=100)
    tokens = budget.allocate("Hello")
    assert tokens > 0
    assert budget.used_tokens > 0


def test_remaining():
    """Test remaining budget."""
    budget = TokenBudget(max_tokens=100)
    budget.allocate("Hello")
    remaining = budget.remaining()
    assert remaining < 100
    assert remaining >= 0


def test_reset():
    """Test budget reset."""
    budget = TokenBudget(max_tokens=100)
    budget.allocate("Hello")
    budget.reset()
    assert budget.used_tokens == 0

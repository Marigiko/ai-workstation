"""Token budget management for context."""

import tiktoken


class TokenBudget:
    """Manage token budget for context."""

    def __init__(self, max_tokens: int, model: str = "gpt-4"):
        """Initialize token budget.

        Args:
            max_tokens: Maximum tokens allowed
            model: Model name for tokenizer selection
        """
        self.max_tokens = max_tokens
        self.used_tokens = 0
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoder.encode(text))

    def can_fit(self, text: str) -> bool:
        """Check if text fits in remaining budget."""
        tokens = self.count_tokens(text)
        return self.used_tokens + tokens <= self.max_tokens

    def allocate(self, text: str) -> int:
        """Allocate tokens for text. Returns tokens allocated."""
        tokens = self.count_tokens(text)
        if self.used_tokens + tokens > self.max_tokens:
            return 0
        self.used_tokens += tokens
        return tokens

    def remaining(self) -> int:
        """Get remaining token budget."""
        return max(0, self.max_tokens - self.used_tokens)

    def reset(self):
        """Reset token budget."""
        self.used_tokens = 0

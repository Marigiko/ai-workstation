"""Core exceptions for the AI Workstation platform."""


class ContractError(Exception):
    """Base exception for contract violations."""

    pass


class ProviderError(ContractError):
    """Error from a provider."""

    def __init__(self, provider: str, message: str, original_error: Exception | None = None):
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"Provider '{provider}': {message}")


class RoutingError(ContractError):
    """Error from the router."""

    def __init__(self, message: str):
        super().__init__(f"Routing error: {message}")


class ToolError(ContractError):
    """Error from a tool execution."""

    def __init__(self, tool_name: str, message: str, original_error: Exception | None = None):
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}': {message}")

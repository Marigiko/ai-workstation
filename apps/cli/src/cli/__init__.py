"""AI Workstation CLI package."""

__version__ = "0.1.0"

from cli.client import GatewayClient
from cli.main import app

__all__ = ["GatewayClient", "app"]

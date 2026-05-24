"""Manages persistent Hermes session IDs per repository."""
import os
from hermes_client import HermesClient

_client: HermesClient | None = None


def get_hermes_client() -> HermesClient:
    global _client
    if _client is None:
        _client = HermesClient(
            base_url=os.getenv("HERMES_BASE_URL", "http://localhost:11434"),
            api_key=os.getenv("HERMES_API_KEY", "hermes"),
            model=os.getenv("HERMES_MODEL", "hermes"),
        )
    return _client

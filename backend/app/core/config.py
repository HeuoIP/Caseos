"""Centralised application settings for CaseOS backend.

Reads from environment variables when available; otherwise falls back to
defaults so the skeleton can boot without any configuration. Authentication
and database layers are intentionally not part of V0.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    project_name: str = "CaseOS API"
    version: str = "0.1.0"
    api_prefix: str = ""


settings = Settings()

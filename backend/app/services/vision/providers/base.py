"""Provider abstraction for CaseOS vision analyzers.

A ``Provider`` is the thin HTTP layer that talks to one upstream vision
model. It returns the *raw* response string and knows nothing about the
CaseOS schema, taxonomy, or prompts beyond what is passed in.

``CaseVisionAnalyzer`` (``app.services.vision.analyzer``) owns the CaseOS
domain logic (prompt, schema, library, validation). ``Provider`` only owns
the network round-trip.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderResult:
    """Raw response from a vision provider.

    Attributes:
        raw_text: The model's response text (expected to be valid JSON).
        model: Model identifier used for the call.
        finish_reason: Optional metadata from the upstream API.
    """

    raw_text: str
    model: str
    finish_reason: str = ""


class Provider(ABC):
    """Abstract vision provider.

    Implementations wrap one upstream model API (Qwen, Doubao, Claude
    Vision, etc.) and expose only one method: ``complete``.
    """

    @abstractmethod
    def complete(self, prompt: str, image_url: str) -> ProviderResult:
        """Send ``prompt`` + ``image_url`` to the upstream model.

        Args:
            prompt: The full text prompt to send.
            image_url: ``data:`` URL or ``http(s)`` URL of the image.

        Returns:
            A ``ProviderResult`` wrapping the raw JSON text returned by
            the model. This method MUST NOT parse the JSON or apply any
            CaseOS-specific knowledge.
        """
        raise NotImplementedError


__all__ = ["Provider", "ProviderResult"]

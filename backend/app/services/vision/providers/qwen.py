"""Qwen-VL provider for CaseOS.

HTTP-only implementation. Returns the raw JSON text from the model;
schema/taxonomy/prompt concerns live in ``CaseVisionAnalyzer``.

Reads ``QWEN_API_KEY`` from the environment (populated by
``python-dotenv`` at script level).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from app.services.vision.providers.base import Provider, ProviderResult


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.7-plus"
DEFAULT_TIMEOUT = 180


class QwenProvider(Provider):
    """HTTP client for Qwen3.7-Plus via DashScope OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key or os.environ.get("QWEN_API_KEY")
        if not self._api_key:
            raise RuntimeError(
                "QWEN_API_KEY missing. Copy backend/.env.example to backend/.env."
            )
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def complete(self, prompt: str, image_url: str) -> ProviderResult:
        """POST prompt + image_url to DashScope, return raw JSON text.

        Returns:
            ProviderResult whose ``raw_text`` is the model's JSON
            response (parsed once at HTTP boundary; the message content
            itself is JSON because we set ``response_format: json_object``).
        """
        body = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
        }

        request = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as resp:
                payload = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Qwen HTTP {exc.code}: {detail[:500]}") from exc

        obj = json.loads(payload)
        message = obj["choices"][0]["message"]["content"]
        finish = obj["choices"][0].get("finish_reason", "")

        if isinstance(message, str):
            return ProviderResult(raw_text=message, model=self._model, finish_reason=finish)
        if isinstance(message, dict):
            return ProviderResult(
                raw_text=json.dumps(message, ensure_ascii=False),
                model=self._model,
                finish_reason=finish,
            )
        raise RuntimeError(
            f"Unexpected Qwen response payload type: {type(message).__name__}"
        )


__all__ = ["QwenProvider"]

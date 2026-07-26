"""Qwen-VL provider for CaseOS V1.

Makes a single chat-completions call against the DashScope compatible-mode
endpoint using ``qwen3.7-plus``. Reads ``QWEN_API_KEY`` from the environment
(populated by ``python-dotenv`` at script level).
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.services.vision.analyzer import VisionAnalyzer

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.7-plus"
DEFAULT_TIMEOUT = 180


class QwenVisionAnalyzer(VisionAnalyzer):
    """Vision analyzer backed by Qwen3.7-Plus via DashScope."""

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

    def analyze(self, image_path: str, *, prompt: str) -> dict[str, Any]:
        """Run the vision model on ``image_path`` using ``prompt``.

        Returns:
            The parsed CaseOS analysis JSON returned by the model.
        """

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(image_path)

        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        image_data_url = f"data:image/png;base64,{encoded}"

        body = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_data_url}},
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

        if isinstance(message, str):
            return json.loads(message)
        if isinstance(message, dict):
            return message
        raise RuntimeError(f"Unexpected Qwen response payload: {type(message).__name__}")

from __future__ import annotations

import json
import logging
from typing import Any

import requests

from .utils import append_jsonl


class OllamaClient:
    def __init__(self, url: str, model: str, log_path):
        self.url = url.rstrip("/")
        self.model = model
        self.log_path = log_path

    def call_chat_json(self, messages: list[dict[str, str]], retries: int = 3) -> dict[str, Any]:
        last_error = ""
        for attempt in range(1, retries + 1):
            try:
                res = requests.post(
                    f"{self.url}/api/chat",
                    json={"model": self.model, "messages": messages, "stream": False, "format": "json"},
                    timeout=120,
                )
                res.raise_for_status()
                data = res.json()
                content = data.get("message", {}).get("content", "{}")
                parsed = json.loads(content)
                append_jsonl(self.log_path, {"attempt": attempt, "ok": True, "response": parsed})
                return parsed
            except Exception as e:  # noqa: BLE001
                last_error = str(e)
                logging.warning("Ollama parse/call failed attempt %s: %s", attempt, e)
                append_jsonl(self.log_path, {"attempt": attempt, "ok": False, "error": str(e)})
        raise RuntimeError(f"Ollama failed after retries: {last_error}")

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests


class AutoPoster:
    """Dispatch generated posts to optional platform webhooks.

    This keeps the existing generation flow intact while allowing
    downstream automation tools (Make/Zapier/custom API) to publish.
    """

    def __init__(
        self,
        enabled: bool,
        pinterest_webhook: str | None,
        instagram_webhook: str | None,
        timeout_sec: int = 15,
        dry_run: bool = False,
    ) -> None:
        self.enabled = enabled
        self.timeout_sec = timeout_sec
        self.dry_run = dry_run
        self.webhooks = {
            "pinterest": (pinterest_webhook or "").strip(),
            "instagram": (instagram_webhook or "").strip(),
        }

    def post(self, platform: str, payload: dict[str, Any], asset_path: Path) -> bool:
        if not self.enabled:
            return False

        webhook = self.webhooks.get(platform, "")
        if not webhook:
            logging.info("Auto-post skipped (%s): webhook not configured", platform)
            return False

        body = {
            "platform": platform,
            "date": payload.get("date"),
            "topic": payload.get("topic", {}),
            "item": payload.get("item", {}),
            "asset_path": str(asset_path),
            "meta": payload.get(platform, {}),
            "image_text": payload.get("image_text", {}),
            "seed": payload.get("seed"),
        }

        if self.dry_run:
            logging.info("Auto-post dry-run (%s): %s", platform, body)
            return True

        try:
            resp = requests.post(webhook, json=body, timeout=self.timeout_sec)
            resp.raise_for_status()
            logging.info("Auto-post success (%s): status=%s", platform, resp.status_code)
            return True
        except requests.RequestException as exc:
            logging.warning("Auto-post failed (%s): %s", platform, exc)
            return False

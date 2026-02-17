from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import requests


class SocialAutoPoster:
    """Publish generated assets to Pinterest/Instagram APIs."""

    def __init__(
        self,
        *,
        enabled: bool,
        dry_run: bool,
        timeout_sec: int,
        asset_public_base_url: str | None,
        pinterest_access_token: str | None,
        pinterest_board_id: str | None,
        instagram_access_token: str | None,
        instagram_user_id: str | None,
    ) -> None:
        self.enabled = enabled
        self.dry_run = dry_run
        self.timeout_sec = timeout_sec
        self.asset_public_base_url = (asset_public_base_url or "").rstrip("/")

        self.pinterest_access_token = (pinterest_access_token or "").strip()
        self.pinterest_board_id = (pinterest_board_id or "").strip()
        self.instagram_access_token = (instagram_access_token or "").strip()
        self.instagram_user_id = (instagram_user_id or "").strip()

    def post(self, platform: str, payload: dict[str, Any], asset_path: Path, root_dir: Path) -> bool:
        if not self.enabled:
            return False

        try:
            public_url = self._public_asset_url(asset_path, root_dir)
        except ValueError as exc:
            logging.warning("Auto-post skipped (%s): %s", platform, exc)
            return False

        if self.dry_run:
            logging.info(
                "Auto-post dry-run (%s): asset=%s caption_preview=%s",
                platform,
                public_url,
                self._caption_preview(platform, payload),
            )
            return True

        if platform == "pinterest":
            return self._post_pinterest(payload, public_url)
        if platform == "instagram":
            return self._post_instagram(payload, public_url)

        logging.warning("Auto-post skipped: unsupported platform=%s", platform)
        return False

    def _caption_preview(self, platform: str, payload: dict[str, Any]) -> str:
        if platform == "pinterest":
            meta = payload.get("pinterest", {})
            return str(meta.get("title", ""))
        meta = payload.get("instagram", {})
        hook = str(meta.get("hook", "")).strip()
        caption = str(meta.get("caption", "")).strip()
        return (hook + " " + caption).strip()[:80]

    def _public_asset_url(self, asset_path: Path, root_dir: Path) -> str:
        if not self.asset_public_base_url:
            raise ValueError("SOCIAL_ASSET_PUBLIC_BASE_URL is not configured")

        try:
            rel = asset_path.resolve().relative_to(root_dir.resolve())
        except ValueError as exc:
            raise ValueError(f"asset path is outside repository: {asset_path}") from exc
        rel_posix = rel.as_posix()
        return f"{self.asset_public_base_url}/{rel_posix}"

    def _post_pinterest(self, payload: dict[str, Any], image_url: str) -> bool:
        if not self.pinterest_access_token or not self.pinterest_board_id:
            logging.info("Auto-post skipped (pinterest): missing token or board id")
            return False

        meta = payload.get("pinterest", {})
        title = str(meta.get("title", "")).strip()
        description = str(meta.get("description", "")).strip()
        hashtags = [str(x).strip() for x in meta.get("hashtags", []) if str(x).strip()]
        if hashtags:
            description = (description + "\n\n" + " ".join(hashtags)).strip()
        link = str(meta.get("link", "")).strip() or None

        body: dict[str, Any] = {
            "board_id": self.pinterest_board_id,
            "title": title,
            "description": description,
            "media_source": {
                "source_type": "image_url",
                "url": image_url,
            },
        }
        if link:
            body["link"] = link

        headers = {
            "Authorization": f"Bearer {self.pinterest_access_token}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post("https://api.pinterest.com/v5/pins", headers=headers, json=body, timeout=self.timeout_sec)
            resp.raise_for_status()
            logging.info("Auto-post success (pinterest): status=%s", resp.status_code)
            return True
        except requests.RequestException as exc:
            details = getattr(exc.response, "text", "") if hasattr(exc, "response") else ""
            logging.warning("Auto-post failed (pinterest): %s %s", exc, details[:300])
            return False

    def _post_instagram(self, payload: dict[str, Any], image_url: str) -> bool:
        if not self.instagram_access_token or not self.instagram_user_id:
            logging.info("Auto-post skipped (instagram): missing token or user id")
            return False

        meta = payload.get("instagram", {})
        caption_parts = [str(meta.get("hook", "")).strip(), str(meta.get("caption", "")).strip()]
        hashtags = [str(x).strip() for x in meta.get("hashtags", []) if str(x).strip()]
        if hashtags:
            caption_parts.append(" ".join(hashtags))
        caption = "\n\n".join(part for part in caption_parts if part)

        create_url = f"https://graph.facebook.com/v23.0/{self.instagram_user_id}/media"
        publish_url = f"https://graph.facebook.com/v23.0/{self.instagram_user_id}/media_publish"
        params = {
            "access_token": self.instagram_access_token,
        }

        try:
            create_resp = requests.post(
                create_url,
                params=params,
                data={"image_url": image_url, "caption": caption},
                timeout=self.timeout_sec,
            )
            create_resp.raise_for_status()
            creation_id = str(create_resp.json().get("id", "")).strip()
            if not creation_id:
                logging.warning("Auto-post failed (instagram): missing creation id")
                return False

            if not self._wait_instagram_container(creation_id):
                return False

            publish_resp = requests.post(
                publish_url,
                params=params,
                data={"creation_id": creation_id},
                timeout=self.timeout_sec,
            )
            publish_resp.raise_for_status()
            logging.info("Auto-post success (instagram): status=%s", publish_resp.status_code)
            return True
        except requests.RequestException as exc:
            details = getattr(exc.response, "text", "") if hasattr(exc, "response") else ""
            logging.warning("Auto-post failed (instagram): %s %s", exc, details[:300])
            return False

    def _wait_instagram_container(self, creation_id: str) -> bool:
        status_url = f"https://graph.facebook.com/v23.0/{creation_id}"
        params = {"access_token": self.instagram_access_token, "fields": "status_code"}
        for _ in range(10):
            try:
                resp = requests.get(status_url, params=params, timeout=self.timeout_sec)
                resp.raise_for_status()
                status = str(resp.json().get("status_code", "")).upper()
                if status in {"FINISHED", "PUBLISHED"}:
                    return True
                if status in {"ERROR", "EXPIRED"}:
                    logging.warning("Auto-post failed (instagram): container status=%s", status)
                    return False
            except requests.RequestException as exc:
                logging.warning("Auto-post status check failed (instagram): %s", exc)
                return False
            time.sleep(2)

        logging.warning("Auto-post failed (instagram): timed out waiting container")
        return False

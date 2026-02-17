from __future__ import annotations

from typing import Any

BANNED = ["絶対", "完全に", "最強", "100%", "これで決まり", "迷ったらこれ"]


def _contains_banned(text: str) -> bool:
    return any(b in text for b in BANNED)


def validate_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        headline = payload["image_text"]["headline"]
        if not (30 <= len(headline) <= 70):
            return False, "headline length out of range"
        pin_title = payload["pinterest"]["title"]
        if not (32 <= len(pin_title) <= 60):
            return False, "pinterest title length out of range"
        all_text = "\n".join(
            [
                headline,
                payload["pinterest"].get("description", ""),
                payload["instagram"].get("caption", ""),
            ]
        )
        if _contains_banned(all_text):
            return False, "banned words found"
    except KeyError as e:
        return False, f"missing key: {e}"
    return True, "ok"


def normalize_payload(payload: dict[str, Any], link: str) -> dict[str, Any]:
    payload.setdefault("image_text", {})
    payload.setdefault("pinterest", {})
    payload.setdefault("instagram", {})
    payload["pinterest"].setdefault("hashtags", [])
    payload["instagram"].setdefault("hashtags", [])
    payload["pinterest"]["link_text"] = link
    return payload

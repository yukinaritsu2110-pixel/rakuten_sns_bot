from __future__ import annotations

from typing import Any

BANNED = ["絶対", "完全に", "最強", "100%", "これで決まり", "迷ったらこれ"]


def _contains_banned(text: str) -> bool:
    return any(b in text for b in BANNED)


def _required_string(payload: dict[str, Any], path: tuple[str, str]) -> str:
    parent_key, child_key = path
    parent = payload[parent_key]
    value = parent[child_key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid value at {parent_key}.{child_key}")
    return value.strip()


def validate_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        headline = _required_string(payload, ("image_text", "headline"))
        pin_title = _required_string(payload, ("pinterest", "title"))
        pin_description = _required_string(payload, ("pinterest", "description"))
        ig_hook = _required_string(payload, ("instagram", "hook"))
        ig_caption = _required_string(payload, ("instagram", "caption"))

        if not (30 <= len(headline) <= 70):
            return False, "headline length out of range"
        if not (32 <= len(pin_title) <= 60):
            return False, "pinterest title length out of range"

        all_text = "\n".join([headline, pin_description, ig_hook, ig_caption])
        if _contains_banned(all_text):
            return False, "banned words found"
    except KeyError as e:
        return False, f"missing key: {e}"
    except ValueError as e:
        return False, str(e)
    return True, "ok"


def normalize_payload(payload: dict[str, Any], link: str) -> dict[str, Any]:
    payload.setdefault("image_text", {})
    payload.setdefault("pinterest", {})
    payload.setdefault("instagram", {})
    payload["pinterest"].setdefault("hashtags", [])
    payload["instagram"].setdefault("hashtags", [])
    payload["pinterest"]["link_text"] = link
    return payload

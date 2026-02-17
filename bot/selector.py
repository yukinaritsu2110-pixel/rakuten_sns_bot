from __future__ import annotations

from typing import Any


def _score(item: dict[str, Any], keyword: str) -> float:
    name = item.get("name", "")
    score = 0
    if item.get("image_url"):
        score += 3
    p = item.get("price_yen", 0)
    if 500 <= p <= 50000:
        score += 2
    kw_tokens = [k for k in keyword.split() if k]
    score += sum(1 for t in kw_tokens if t.lower() in name.lower())
    return score


def choose_item(candidates: list[dict[str, Any]], keyword: str) -> dict[str, Any]:
    if not candidates:
        return {
            "item_code": "fallback-item",
            "name": f"{keyword} に合うおすすめアイテム",
            "price_yen": 2980,
            "url": "",
            "affiliate_url": "",
            "image_url": "",
        }
    scored = sorted(candidates, key=lambda x: _score(x, keyword), reverse=True)
    return scored[0]

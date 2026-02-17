from __future__ import annotations

import logging
import time
from typing import Any

import requests


class RakutenAPI:
    endpoint = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"

    def __init__(self, application_id: str, affiliate_id: str | None = None):
        self.application_id = application_id
        self.affiliate_id = affiliate_id

    def search_items(self, keyword: str, genre_id: int | None = None, hits: int = 10) -> list[dict[str, Any]]:
        if not self.application_id:
            return []
        params = {
            "applicationId": self.application_id,
            "keyword": keyword,
            "hits": hits,
            "format": "json",
            "imageFlag": 1,
        }
        if self.affiliate_id:
            params["affiliateId"] = self.affiliate_id
        if genre_id:
            params["genreId"] = genre_id

        for i in range(3):
            r = requests.get(self.endpoint, params=params, timeout=40)
            if r.status_code == 429:
                sleep = 2 ** i
                logging.warning("Rakuten 429 retry in %ss", sleep)
                time.sleep(sleep)
                continue
            r.raise_for_status()
            data = r.json()
            return [x.get("Item", {}) for x in data.get("Items", [])]
        return []

    @staticmethod
    def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
        images = item.get("mediumImageUrls", [])
        image_url = ""
        if images:
            image_url = images[0].get("imageUrl", "")
        return {
            "item_code": item.get("itemCode", "unknown"),
            "name": item.get("itemName", "商品"),
            "price_yen": int(item.get("itemPrice", 0) or 0),
            "url": item.get("itemUrl", ""),
            "affiliate_url": item.get("affiliateUrl") or item.get("itemUrl", ""),
            "image_url": image_url,
        }

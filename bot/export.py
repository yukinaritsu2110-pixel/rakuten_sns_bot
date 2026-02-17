from __future__ import annotations

import csv
import json
from pathlib import Path


def write_meta_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_meta_txt(path: Path, payload: dict, platform: str) -> None:
    if platform == "pinterest":
        text = (
            f"[Title]\n{payload['pinterest']['title']}\n\n"
            f"[Description]\n{payload['pinterest']['description']}\n\n"
            f"[Hashtags]\n{' '.join(payload['pinterest']['hashtags'])}\n\n"
            f"[Link]\n{payload['pinterest']['link']}\n"
        )
    else:
        text = (
            f"[Hook]\n{payload['instagram']['hook']}\n\n"
            f"[Caption]\n{payload['instagram']['caption']}\n\n"
            f"[Hashtags]\n{' '.join(payload['instagram']['hashtags'])}\n\n"
            f"[Link hint]\n{payload['instagram']['link_hint']}\n"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_index_csv(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)

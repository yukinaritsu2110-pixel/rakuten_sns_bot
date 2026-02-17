from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _simple_env_load(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    """Minimal YAML loader for this project if PyYAML is unavailable."""
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        text = path.read_text(encoding="utf-8")
        # fallback: accept JSON content in .yaml files
        return json.loads(text)


@dataclass
class EnvConfig:
    rakuten_application_id: str
    rakuten_affiliate_id: str | None
    ollama_model: str
    ollama_url: str
    brand_name: str
    default_days: int
    auto_post_enabled: bool
    auto_post_timeout_sec: int
    social_asset_public_base_url: str | None
    pinterest_access_token: str | None
    pinterest_board_id: str | None
    instagram_access_token: str | None
    instagram_user_id: str | None


@dataclass
class AppConfig:
    root_dir: Path
    env: EnvConfig
    account: dict[str, Any]
    topics: list[dict[str, Any]]


def load_app_config(root_dir: Path) -> AppConfig:
    _simple_env_load(root_dir / ".env")
    account = _load_simple_yaml(root_dir / "config" / "account.yaml")
    topics_doc = _load_simple_yaml(root_dir / "config" / "topics.yaml")

    env = EnvConfig(
        rakuten_application_id=os.getenv("RAKUTEN_APPLICATION_ID", ""),
        rakuten_affiliate_id=os.getenv("RAKUTEN_AFFILIATE_ID") or None,
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        brand_name=os.getenv("BRAND_NAME", account.get("brand_name", "brand")),
        default_days=int(os.getenv("DEFAULT_DAYS", "7")),
        auto_post_enabled=os.getenv("AUTO_POST_ENABLED", "false").lower() in {"1", "true", "yes", "on"},
        auto_post_timeout_sec=int(os.getenv("AUTO_POST_TIMEOUT_SEC", "20")),
        social_asset_public_base_url=os.getenv("SOCIAL_ASSET_PUBLIC_BASE_URL") or None,
        pinterest_access_token=os.getenv("PINTEREST_ACCESS_TOKEN") or None,
        pinterest_board_id=os.getenv("PINTEREST_BOARD_ID") or None,
        instagram_access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN") or None,
        instagram_user_id=os.getenv("INSTAGRAM_USER_ID") or None,
    )
    topics = topics_doc.get("topics", [])
    return AppConfig(root_dir=root_dir, env=env, account=account, topics=topics)

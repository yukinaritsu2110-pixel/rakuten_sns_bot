from __future__ import annotations

import argparse
import logging
from datetime import date, datetime
from pathlib import Path

from bot.config import load_app_config
from bot.copywriter import normalize_payload, validate_payload
from bot.export import append_index_csv, write_meta_json, write_meta_txt
from bot.ollama_client import OllamaClient
from bot.prompt_loader import load_prompts, render_prompt
from bot.rakuten_api import RakutenAPI
from bot.render import render_instagram_feed, render_pinterest
from bot.selector import choose_item
from bot.social_api import SocialAutoPoster
from bot.utils import date_range, init_logging, stable_seed
from bot.video import make_reel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=None)
    parser.add_argument("--start", type=str, default=None)
    parser.add_argument("--platform", choices=["pinterest", "instagram", "both"], default="both")
    parser.add_argument("--autopost", action="store_true", help="Generate and then publish via Pinterest/Instagram APIs")
    parser.add_argument("--autopost-dry-run", action="store_true", help="Log API payload intent without posting")
    return parser.parse_args()


def fallback_copy(topic: dict, item: dict) -> dict:
    name = topic.get("name", "暮らしの工夫")
    kws = topic.get("intent", {}).get("keywords", [])
    tags = [f"#{k}" for k in kws[:10]] or ["#暮らし", "#楽天購入品"]
    return {
        "image_text": {
            "headline": "視界を整える小さな工夫で、毎日の作業や片づけが少しラクになるアイテム選び。",
            "subline": "戻しやすさを先に作る",
            "note": "無理なく続く",
        },
        "pinterest": {
            "title": f"{name}で整える、暮らしに馴染むアイテム選びのヒント",
            "description": f"{item['name']}を中心に、生活動線を崩しにくい使い方を想定した投稿です。必要以上に増やさず、戻しやすく、続けやすいを意識しています。",
            "hashtags": tags[:8],
            "link_text": item.get("affiliate_url") or item.get("url") or "",
        },
        "instagram": {
            "hook": "整えるほど、暮らしが静かに。",
            "caption": f"{item['name']}を使って、視界のノイズを減らす工夫をまとめました。\n\n片づけより先に、戻せる仕組みを作ると続けやすいです。",
            "hashtags": tags,
        },
        "alt_text": f"{item['name']}を使ったミニマルな暮らし向け投稿ビジュアル",
    }


def safe_slug(text: str) -> str:
    """Create a filesystem-safe slug for output filenames."""
    keep = []
    for ch in text:
        if ch.isalnum() or ch in ("-", "_"):
            keep.append(ch)
        else:
            keep.append("_")
    slug = "".join(keep).strip("_")
    return slug or "item"


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    cfg = load_app_config(root)

    days = args.days or cfg.env.default_days
    start = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else date.today()
    run_log = root / "logs" / f"{date.today():%Y-%m-%d}_run.log"
    init_logging(run_log)

    prompts = load_prompts(root)
    ollama = OllamaClient(cfg.env.ollama_url, cfg.env.ollama_model, root / "logs" / "llm_calls.jsonl")
    rakuten = RakutenAPI(cfg.env.rakuten_application_id, cfg.env.rakuten_affiliate_id)

    autoposter = SocialAutoPoster(
        enabled=cfg.env.auto_post_enabled or args.autopost,
        dry_run=args.autopost_dry_run,
        timeout_sec=cfg.env.auto_post_timeout_sec,
        asset_public_base_url=cfg.env.social_asset_public_base_url,
        pinterest_access_token=cfg.env.pinterest_access_token,
        pinterest_board_id=cfg.env.pinterest_board_id,
        instagram_access_token=cfg.env.instagram_access_token,
        instagram_user_id=cfg.env.instagram_user_id,
    )

    for d in date_range(start, days):
        slides_for_reel = []
        for topic in cfg.topics:
            keyword = topic.get("search", {}).get("keyword", topic.get("name", ""))
            genre_id = topic.get("search", {}).get("genre_id")
            raw_items = rakuten.search_items(keyword=keyword, genre_id=genre_id, hits=12)
            candidates = [rakuten.normalize_item(x) for x in raw_items]
            item = choose_item(candidates, keyword)

            seed = stable_seed([str(d), topic.get("id", "t"), item.get("item_code", "x")])
            context = {
                "seed": seed,
                "brand": cfg.account.get("brand_name", cfg.env.brand_name),
                "tone": cfg.account.get("tone", {}),
                "topic": topic,
                "item": item,
                "platforms": ["pinterest", "instagram"],
            }

            llm_data = fallback_copy(topic, item)
            try:
                messages = render_prompt(prompts, context)
                for _ in range(3):
                    candidate = ollama.call_chat_json(messages)
                    ok, reason = validate_payload(candidate)
                    if ok:
                        llm_data = candidate
                        break
                    logging.warning("LLM validation failed: %s", reason)
            except Exception as e:  # noqa: BLE001
                logging.warning("Using fallback copy due to LLM issue: %s", e)

            llm_data = normalize_payload(llm_data, item.get("affiliate_url") or item.get("url") or "")

            payload = {
                "date": str(d),
                "topic": {"id": topic.get("id"), "name": topic.get("name")},
                "item": item,
                "pinterest": {
                    "title": llm_data["pinterest"]["title"],
                    "description": llm_data["pinterest"]["description"],
                    "hashtags": llm_data["pinterest"]["hashtags"],
                    "link": llm_data["pinterest"]["link_text"],
                },
                "instagram": {
                    "hook": llm_data["instagram"]["hook"],
                    "caption": llm_data["instagram"]["caption"],
                    "hashtags": llm_data["instagram"]["hashtags"],
                    "link_hint": "プロフィールリンクへ",
                },
                "image_text": llm_data["image_text"],
                "seed": seed,
            }

            topic_id = safe_slug(str(topic.get("id", "topic")))
            item_code = safe_slug(str(item.get("item_code", "item")))
            id_base = f"{topic_id}_{item_code}"
            day_dir = root / "output" / str(d)

            pin_path = day_dir / "pinterest" / "pins" / f"pin_{id_base}.jpg"
            ig_img_path = day_dir / "instagram" / "images" / f"ig_{id_base}_feed.jpg"
            p_json = day_dir / "pinterest" / "meta" / f"post_{id_base}.json"
            p_txt = day_dir / "pinterest" / "meta" / f"post_{id_base}.txt"
            i_json = day_dir / "instagram" / "meta" / f"post_{id_base}.json"
            i_txt = day_dir / "instagram" / "meta" / f"post_{id_base}.txt"

            if args.platform in ("pinterest", "both"):
                render_pinterest(pin_path, item, topic.get("name", ""), payload["image_text"], cfg.account, cfg.env.brand_name)
                write_meta_json(p_json, payload)
                write_meta_txt(p_txt, payload, "pinterest")
                append_index_csv(day_dir / "pinterest" / "index.csv", {"topic_id": topic.get("id"), "item_code": item.get("item_code"), "pin": str(pin_path)})
                autoposter.post("pinterest", payload, pin_path, root)
                slides_for_reel.append(pin_path)

            if args.platform in ("instagram", "both"):
                if not pin_path.exists():
                    render_pinterest(pin_path, item, topic.get("name", ""), payload["image_text"], cfg.account, cfg.env.brand_name)
                if pin_path not in slides_for_reel:
                    slides_for_reel.append(pin_path)
                render_instagram_feed(ig_img_path, pin_path, cfg.account)
                write_meta_json(i_json, payload)
                write_meta_txt(i_txt, payload, "instagram")
                append_index_csv(day_dir / "instagram" / "index.csv", {"topic_id": topic.get("id"), "item_code": item.get("item_code"), "image": str(ig_img_path)})
                autoposter.post("instagram", payload, ig_img_path, root)

        if args.platform in ("instagram", "both") and slides_for_reel:
            reel_path = root / "output" / str(d) / "instagram" / "reels" / f"reel_{d}.mp4"
            if not make_reel(slides_for_reel, reel_path):
                logging.info("Reel generation skipped (ffmpeg unavailable or failed)")


if __name__ == "__main__":
    main()

from __future__ import annotations

import io
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size=size)
    except Exception:  # noqa: BLE001
        return ImageFont.load_default()


def _download_image(url: str) -> Image.Image | None:
    if not url:
        return None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:  # noqa: BLE001
        return None


def _fit_text(draw, text, font_path, max_width, max_lines, start_size=54, min_size=24):
    for size in range(start_size, min_size - 1, -2):
        font = _load_font(font_path, size)
        lines = []
        current = ""
        for ch in text:
            trial = current + ch
            w = draw.textbbox((0, 0), trial, font=font)[2]
            if w <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
        if len(lines) <= max_lines:
            return lines, font
    return [text[: max(1, len(text) // 2)] + "…"], _load_font(font_path, min_size)


def _render_base(size, item_image, colors):
    w, h = size
    bg = Image.new("RGB", (w, h), tuple(colors["bg"]))
    if item_image:
        bgfit = item_image.resize((w, h)).filter(ImageFilter.GaussianBlur(20))
        bg = Image.blend(bg, bgfit, alpha=0.35)
    card = Image.new("RGB", (w - 80, h - 80), tuple(colors["card"]))
    bg.paste(card, (40, 40))
    return bg


def render_pinterest(path: Path, item: dict, topic_name: str, image_text: dict, account: dict, brand_name: str) -> None:
    colors = account["theme"]["colors"]
    fonts = account["theme"]["font"]
    img = _download_image(item.get("image_url", ""))
    canvas = _render_base((1000, 1500), img, colors)
    draw = ImageDraw.Draw(canvas)
    bold = fonts.get("bold") or fonts.get("regular")
    regular = fonts.get("regular")

    draw.rounded_rectangle((80, 80, 520, 150), radius=35, fill=(240, 240, 240))
    draw.text((105, 100), topic_name[:28], fill=tuple(colors["text"]), font=_load_font(bold, 32))

    if img:
        img.thumbnail((780, 650))
        x = (1000 - img.width) // 2
        y = 230
        canvas.paste(img, (x, y))

    headline = image_text.get("headline", "")
    lines, font = _fit_text(draw, headline, bold, 820, 3, start_size=58)
    y = 940
    for ln in lines:
        draw.text((90, y), ln, fill=tuple(colors["text"]), font=font)
        y += font.size + 8

    subline = image_text.get("subline", "")
    if subline:
        draw.text((90, y + 10), subline[:40], fill=tuple(colors["muted"]), font=_load_font(regular, 32))

    draw.text((830, 1360), f"¥{item.get('price_yen',0):,}", fill=tuple(colors["muted"]), font=_load_font(regular, 28))
    draw.text((800, 1430), brand_name, fill=tuple(colors["muted"]), font=_load_font(regular, 24))

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, "JPEG", quality=92)


def render_instagram_feed(path: Path, pin_path: Path, account: dict) -> None:
    img = Image.open(pin_path).convert("RGB")
    out = Image.new("RGB", (1080, 1350), tuple(account["theme"]["colors"]["bg"]))
    img.thumbnail((1080, 1350))
    x = (1080 - img.width) // 2
    y = (1350 - img.height) // 2
    out.paste(img, (x, y))
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path, "JPEG", quality=92)

from __future__ import annotations

import json
from pathlib import Path


PROMPT_FILES = ["system.txt", "common_rules.txt", "pinterest.txt", "instagram.txt"]


def load_prompts(root_dir: Path) -> dict[str, str]:
    prompts_dir = root_dir / "prompts"
    prompts = {}
    for name in PROMPT_FILES:
        prompts[name] = (prompts_dir / name).read_text(encoding="utf-8")
    return prompts


def render_prompt(prompts: dict[str, str], context: dict) -> list[dict[str, str]]:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    user_content = "\n\n".join(
        [
            prompts["common_rules.txt"],
            prompts["pinterest.txt"],
            prompts["instagram.txt"],
            "# context_json",
            context_json,
        ]
    )
    return [
        {"role": "system", "content": prompts["system.txt"]},
        {"role": "user", "content": user_content},
    ]

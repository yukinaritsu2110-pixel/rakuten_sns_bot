# Rakuten SNS Creator

楽天商品を元に Pinterest / Instagram 向けの画像・文章を日付管理で出力する CLI ツールです。

## セットアップ

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

`.env` を作成:

```env
RAKUTEN_APPLICATION_ID=
RAKUTEN_AFFILIATE_ID=
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_URL=http://localhost:11434
BRAND_NAME=ゆきな
DEFAULT_DAYS=7
```

## 実行

```bash
python -m scripts.run
python -m scripts.run --days 14
python -m scripts.run --start 2026-02-20
python -m scripts.run --platform pinterest
python -m scripts.run --platform instagram
```

## 出力

- `output/YYYY-MM-DD/pinterest/...`
- `output/YYYY-MM-DD/instagram/...`
- `logs/YYYY-MM-DD_run.log`
- `logs/llm_calls.jsonl`

> フォントが未配置でも実行は可能です（Pillowのデフォルトフォントにフォールバック）。

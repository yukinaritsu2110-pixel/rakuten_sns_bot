# Rakuten SNS Creator

楽天商品を元に Pinterest / Instagram 向けの画像・文章を日付管理で出力する CLI ツールです。

## セットアップ

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### セットアップコマンドの意味

- `python -m venv .venv`
  - このプロジェクト専用の Python 仮想環境を `.venv` に作成します。
- `. .venv/bin/activate`（Windows は `.venv\\Scripts\\activate`）
  - 仮想環境を有効化し、この後の `python` / `pip` がプロジェクト専用環境を使うようになります。
- `pip install -r requirements.txt`
  - `requirements.txt` にある依存（Pillow / requests / python-dotenv / PyYAML）をインストールします。

`.env` を作成:

```env
RAKUTEN_APPLICATION_ID=
RAKUTEN_AFFILIATE_ID=
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_URL=http://localhost:11434
BRAND_NAME=ゆきな
DEFAULT_DAYS=7
AUTO_POST_ENABLED=false
AUTO_POST_PINTEREST_WEBHOOK=
AUTO_POST_INSTAGRAM_WEBHOOK=
AUTO_POST_TIMEOUT_SEC=15
```

## 実行

```bash
python -m scripts.run
python -m scripts.run --days 14
python -m scripts.run --start 2026-02-20
python -m scripts.run --platform pinterest
python -m scripts.run --platform instagram
python -m scripts.run --autopost
python -m scripts.run --autopost --autopost-dry-run
```

### 実行コマンドで何が行われるか

- `python -m scripts.run`
  - `scripts/run.py` の CLI エントリを実行します。
  - `.env` と `config/*.yaml` を読み込み、**今日の日付から `DEFAULT_DAYS` 日数分**の投稿素材を生成します。
  - 各 topic について Rakuten 商品を検索し、Ollama で文章生成して、Pinterest と Instagram 両方の画像・meta・index を出力します。

- `python -m scripts.run --days 14`
  - 生成日数を 14 日に上書きして実行します（開始日は指定がなければ今日）。

- `python -m scripts.run --start 2026-02-20`
  - 開始日を `2026-02-20` に固定して実行します（期間は `DEFAULT_DAYS` または `--days`）。

- `python -m scripts.run --platform pinterest`
  - Pinterest 用のみ生成します。
  - 生成対象: `pins/*.jpg`、`meta/*.json`、`meta/*.txt`、`index.csv`。

- `python -m scripts.run --platform instagram`
  - Instagram 用のみ生成します。
  - 生成対象: `images/*_feed.jpg`、`meta/*.json`、`meta/*.txt`、`index.csv`。
  - 可能なら `reels/*.mp4` も生成します（ffmpeg が利用可能な場合）。

- `python -m scripts.run --autopost`
  - 生成完了後に、設定済みWebhookへ自動投稿リクエストを送信します。
  - 送信先は `.env` の `AUTO_POST_PINTEREST_WEBHOOK` / `AUTO_POST_INSTAGRAM_WEBHOOK` です。
  - 失敗しても生成処理は継続します（ログに warning を出力）。

- `python -m scripts.run --autopost --autopost-dry-run`
  - Webhook送信は行わず、送信予定ペイロードだけをログ出力します。
  - 本番投入前の確認に使えます。

## 出力

- `output/YYYY-MM-DD/pinterest/...`
- `output/YYYY-MM-DD/instagram/...`
- `logs/YYYY-MM-DD_run.log`
- `logs/llm_calls.jsonl`

> フォントが未配置でも実行は可能です（Pillowのデフォルトフォントにフォールバック）。


## 自動投稿の連携仕様

自動投稿は **Webhook連携方式** です。各SNS公式APIへ直接投稿するのではなく、
Make / Zapier / n8n / 自作API などに POST して、そこで最終投稿処理を行います。

Webhook には次のJSONを送ります（主要項目）:
- `platform`: `pinterest` または `instagram`
- `date`, `topic`, `item`
- `asset_path`: ローカル生成画像パス
- `meta`: SNSごとの本文・ハッシュタグ
- `image_text`, `seed`

> 注意: `asset_path` はローカルパスです。外部サービスに渡す場合は、Webhook受信側でアップロード処理を実装してください。

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
AUTO_POST_TIMEOUT_SEC=20
SOCIAL_ASSET_PUBLIC_BASE_URL=https://example.com/rakuten_sns_bot
PINTEREST_ACCESS_TOKEN=
PINTEREST_BOARD_ID=
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_USER_ID=
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
# または dry-run のみ（自動的に投稿処理を有効化）
python -m scripts.run --autopost-dry-run
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
  - 画像/テキスト生成後に Pinterest API / Instagram Graph API へ投稿を試みます。
  - 既存CLI互換（`--days`/`--start`/`--platform`）は維持され、追加オプションとして動きます。

- `python -m scripts.run --autopost --autopost-dry-run`
  - APIには送信せず、投稿対象やcaptionプレビューのみログ出力します。
  - `--autopost-dry-run` 単独指定でも dry-run として動作します。

## 出力

- `output/YYYY-MM-DD/pinterest/...`
- `output/YYYY-MM-DD/instagram/...`
- `logs/YYYY-MM-DD_run.log`
- `logs/llm_calls.jsonl`

> フォントが未配置でも実行は可能です（Pillowのデフォルトフォントにフォールバック）。

## API自動投稿の前提

- Pinterest / Instagram の両APIとも、投稿画像URLは**外部から到達可能な公開URL**である必要があります。
- そのため `SOCIAL_ASSET_PUBLIC_BASE_URL` を設定し、`output/...` の画像をそのURL配下で参照できるようにしてください。
  - 例: `SOCIAL_ASSET_PUBLIC_BASE_URL=https://cdn.example.com/rakuten_sns_bot`
  - 生成画像 `output/2026-02-20/pinterest/pins/pin_x.jpg` は
    `https://cdn.example.com/rakuten_sns_bot/output/2026-02-20/pinterest/pins/pin_x.jpg` として解決されます。
- Instagram は Graph API の公開条件（ビジネス/クリエイターアカウント連携など）を満たす必要があります。

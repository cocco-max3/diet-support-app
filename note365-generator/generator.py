import json
import os
import time
from datetime import datetime
from pathlib import Path

import anthropic

_ENV_FILE = Path(__file__).parent / ".env"

def _load_env_file():
    """`.env` ファイルがあれば環境変数に読み込む"""
    if not _ENV_FILE.exists():
        return
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

_load_env_file()

from prompts import build_prompt, parse_response, build_markdown
from utils import (
    log, log_error, log_skip, log_info,
    save_markdown, append_csv, update_csv_row,
    load_progress, mark_completed, mark_failed,
)

CONFIG_PATH = Path(__file__).parent / "config.json"

RETRY_COUNT = 3
RETRY_WAIT = [5, 10, 20]
OVERLOAD_WAIT = [15, 30, 60]
ARTICLE_WAIT = 5
MODEL = "claude-sonnet-4-6"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def day_to_month_and_index(day: int, config: dict) -> tuple[int, int, str, str]:
    """day番号（1〜365）から月・月内インデックス・テーマ・切り口を返す"""
    months = config["months"]
    cumulative = 0
    for month_num in range(1, 13):
        month_data = months[str(month_num)]
        days_in_month = month_data["days"]
        if cumulative + days_in_month >= day:
            idx = day - cumulative - 1
            angle = month_data["angles"][idx]
            theme = month_data["theme"]
            return month_num, idx, theme, angle
        cumulative += days_in_month
    raise ValueError(f"Day {day} is out of range")


def get_recent_angles(month: int, day_idx: int, config: dict) -> list[str]:
    """同月内の直近5日分の切り口を返す（重複防止用）"""
    angles = config["months"][str(month)]["angles"]
    start = max(0, day_idx - 5)
    return angles[start:day_idx]


def generate_one(
    client: anthropic.Anthropic,
    day: int,
    config: dict,
    force: bool = False
) -> bool:
    """1記事を生成して保存する。成功したらTrueを返す"""
    progress = load_progress()

    if not force and day in progress["completed"]:
        log_skip(day, 365)
        return True

    month, day_idx, theme, angle = day_to_month_and_index(day, config)
    recent_angles = get_recent_angles(month, day_idx, config)
    prompt = build_prompt(day, month, theme, angle, recent_angles)

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text
            article = parse_response(raw_text)

            if not article["title"]:
                raise ValueError("タイトルのパースに失敗しました")

            markdown = build_markdown(article, day, month, theme, angle)
            save_markdown(markdown, day)

            csv_row = {
                "day": day,
                "filename": f"day{day:03d}.md",
                "title": article["title"],
                "month": month,
                "theme": theme,
                "angle": angle,
                "tags": ", ".join(article["tags"]),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "status": "done",
            }
            update_csv_row(day, csv_row)

            mark_completed(day, progress)
            log(day, 365, article["title"], status="done",
                extra=f"{month}月/{angle[:15]}…")
            return True

        except anthropic.RateLimitError as e:
            wait = OVERLOAD_WAIT[attempt - 1]
            log_error(day, 365, f"レート制限 ({e})", attempt)
            if attempt < RETRY_COUNT:
                log_info(f"  {wait}秒待機してリトライします...")
                time.sleep(wait)
        except anthropic.APIStatusError as e:
            if e.status_code == 529:
                wait = OVERLOAD_WAIT[min(attempt - 1, len(OVERLOAD_WAIT) - 1)]
                log_error(day, 365, f"API過負荷 (Overloaded)", attempt)
                if attempt < RETRY_COUNT:
                    log_info(f"  {wait}秒待機してリトライします...")
                    time.sleep(wait)
                else:
                    log_info(f"  スキップして次へ進みます")
            else:
                log_error(day, 365, f"APIエラー ({e})", attempt)
                if attempt < RETRY_COUNT:
                    time.sleep(RETRY_WAIT[attempt - 1])
        except anthropic.APIError as e:
            log_error(day, 365, f"APIエラー ({e})", attempt)
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_WAIT[attempt - 1])
        except Exception as e:
            log_error(day, 365, str(e), attempt)
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_WAIT[attempt - 1])

    mark_failed(day, load_progress())
    return False


def run(start: int = 1, end: int = 365, force: bool = False):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("環境変数 ANTHROPIC_API_KEY が設定されていません。")

    client = anthropic.Anthropic(api_key=api_key)
    config = load_config()

    total_days = end - start + 1
    log_info(f"生成開始: Day {start}〜{end}（{total_days}記事）モデル: {MODEL}")
    log_info(f"ジャンル: {config['genre']}")

    success = 0
    fail = 0

    for day in range(start, end + 1):
        ok = generate_one(client, day, config, force=force)
        if ok:
            success += 1
        else:
            fail += 1

        if day < end:
            time.sleep(ARTICLE_WAIT)

    log_info(f"\n完了: 成功 {success} 記事 / 失敗 {fail} 記事")


def retry_failed():
    """失敗した記事だけ再試行する"""
    progress = load_progress()
    failed_days = sorted(progress["failed"])
    if not failed_days:
        log_info("失敗記事はありません。")
        return

    log_info(f"失敗記事のリトライ: {failed_days}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("環境変数 ANTHROPIC_API_KEY が設定されていません。")

    client = anthropic.Anthropic(api_key=api_key)
    config = load_config()

    for day in failed_days:
        generate_one(client, day, config, force=True)
        time.sleep(ARTICLE_WAIT)

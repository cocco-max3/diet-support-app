import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
CSV_PATH = OUTPUT_DIR / "articles.csv"
PROGRESS_PATH = Path(__file__).parent / "progress.json"

CSV_HEADER = ["day", "filename", "title", "month", "theme", "angle", "tags", "generated_at", "status"]


def ensure_output_dir():
    OUTPUT_DIR.mkdir(exist_ok=True)


def log(day: int, total: int, title: str, status: str = "done", extra: str = ""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    day_str = f"Day {day:03d}/{total}"
    status_icon = "✓" if status == "done" else ("✗" if status == "error" else "→")
    msg = f"[{timestamp}] {status_icon} {day_str} 生成完了  「{title}」"
    if extra:
        msg += f"  ({extra})"
    print(msg, flush=True)


def log_skip(day: int, total: int):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] - Day {day:03d}/{total} スキップ（生成済み）", flush=True)


def log_error(day: int, total: int, error: str, attempt: int):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] ✗ Day {day:03d}/{total} エラー（試行{attempt}/3）: {error}", flush=True)


def log_info(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def save_markdown(content: str, day: int) -> Path:
    ensure_output_dir()
    filename = f"day{day:03d}.md"
    filepath = OUTPUT_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def load_progress() -> dict:
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"completed": [], "failed": [], "last_updated": None}


def save_progress(progress: dict):
    progress["last_updated"] = datetime.now().isoformat()
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def mark_completed(day: int, progress: dict):
    if day not in progress["completed"]:
        progress["completed"].append(day)
    if day in progress["failed"]:
        progress["failed"].remove(day)
    save_progress(progress)


def mark_failed(day: int, progress: dict):
    if day not in progress["failed"]:
        progress["failed"].append(day)
    save_progress(progress)


def init_csv():
    ensure_output_dir()
    if not CSV_PATH.exists():
        with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)


def append_csv(row: dict):
    ensure_output_dir()
    init_csv()
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writerow(row)


def update_csv_row(day: int, row: dict):
    """CSVの該当行を上書きする（再生成時用）"""
    ensure_output_dir()
    if not CSV_PATH.exists():
        init_csv()
        append_csv(row)
        return

    rows = []
    updated = False
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("day") == str(day):
                rows.append(row)
                updated = True
            else:
                rows.append(r)

    if not updated:
        rows.append(row)

    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def print_status(progress: dict, total: int = 365):
    completed = len(progress["completed"])
    failed = len(progress["failed"])
    remaining = total - completed
    print(f"\n{'='*50}")
    print(f"  生成状況レポート")
    print(f"{'='*50}")
    print(f"  完了: {completed} / {total} 記事")
    print(f"  残り: {remaining} 記事")
    if failed:
        print(f"  失敗（要リトライ）: {failed} 記事  → {sorted(progress['failed'])}")
    if progress["last_updated"]:
        print(f"  最終更新: {progress['last_updated']}")
    print(f"{'='*50}\n")

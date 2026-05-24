#!/usr/bin/env python3
"""
note365-generator
副業・個人で稼ぐ力をテーマにした有料note記事を365日分自動生成するツール

使い方:
  python main.py                      # 全365記事を生成（途中から再開）
  python main.py --start 1 --end 30  # 1〜30日目のみ生成
  python main.py --resume             # 未生成の記事のみ生成（--start/--endと組み合わせ可）
  python main.py --day 45 --force     # 45日目だけ強制再生成
  python main.py --status             # 進捗状況を表示
  python main.py --retry-failed       # 失敗した記事だけ再試行
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import load_progress, print_status, log_info
from generator import run, retry_failed, load_config


def parse_args():
    parser = argparse.ArgumentParser(
        description="note365-generator: 副業記事を365日分自動生成します"
    )
    parser.add_argument(
        "--start", type=int, default=1,
        help="生成開始日（デフォルト: 1）"
    )
    parser.add_argument(
        "--end", type=int, default=365,
        help="生成終了日（デフォルト: 365）"
    )
    parser.add_argument(
        "--day", type=int, default=None,
        help="特定の1日のみ生成（--startと--endより優先）"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="未生成の記事のみ生成（生成済みをスキップ）"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="生成済みの記事も上書き再生成する"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="生成状況を表示して終了"
    )
    parser.add_argument(
        "--retry-failed", action="store_true",
        help="失敗した記事だけ再試行する"
    )
    return parser.parse_args()


def validate_range(start: int, end: int):
    if not (1 <= start <= 365):
        sys.exit(f"エラー: --start は1〜365の範囲で指定してください（指定値: {start}）")
    if not (1 <= end <= 365):
        sys.exit(f"エラー: --end は1〜365の範囲で指定してください（指定値: {end}）")
    if start > end:
        sys.exit(f"エラー: --start ({start}) は --end ({end}) 以下にしてください")


def main():
    args = parse_args()

    if args.status:
        progress = load_progress()
        print_status(progress)
        return

    if args.retry_failed:
        retry_failed()
        return

    if args.day is not None:
        validate_range(args.day, args.day)
        log_info(f"Day {args.day} を{'強制再' if args.force else ''}生成します")
        run(start=args.day, end=args.day, force=args.force)
        return

    start = args.start
    end = args.end
    validate_range(start, end)

    if args.resume:
        progress = load_progress()
        completed = set(progress["completed"])
        pending = [d for d in range(start, end + 1) if d not in completed]
        if not pending:
            log_info("指定範囲内の記事はすべて生成済みです。")
            print_status(progress)
            return
        log_info(f"再開モード: {len(pending)} 記事が未生成")
        start_actual = pending[0]
        end_actual = pending[-1]
        run(start=start_actual, end=end_actual, force=False)
    else:
        run(start=start, end=end, force=args.force)

    progress = load_progress()
    print_status(progress)


if __name__ == "__main__":
    main()

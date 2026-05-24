"""
全記事（.md）の末尾タグ行の直前にURLを差し込むスクリプト
"""
import re
from pathlib import Path

INSERT_URL = "https://note.com/takenakaerina/n/nf4e1bb2cb595"
OUTPUT_DIR = Path(__file__).parent / "output"

URL_BLOCK = f"\n---\n\n▷ あわせて読む\n{INSERT_URL}\n"


def update_md(filepath: Path) -> bool:
    text = filepath.read_text(encoding="utf-8")

    # すでに挿入済みの場合はスキップ
    if INSERT_URL in text:
        return False

    # タグ行（#タグ）の直前に挿入
    # 末尾パターン: "---\n#タグ1 #タグ2..."
    new_text = re.sub(
        r"\n---\n(#[^\n]+)$",
        URL_BLOCK + r"---\n\1",
        text,
        flags=re.MULTILINE
    )

    if new_text == text:
        # パターンにマッチしなかった場合は末尾に追加
        new_text = text.rstrip() + URL_BLOCK

    filepath.write_text(new_text, encoding="utf-8")
    return True


def main():
    md_files = sorted(OUTPUT_DIR.glob("day*.md"))
    updated = 0
    for f in md_files:
        if update_md(f):
            updated += 1
    print(f"更新完了: {updated} / {len(md_files)} 記事")


if __name__ == "__main__":
    main()

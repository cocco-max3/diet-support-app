"""
note.com インポート用ファイルを生成するスクリプト

出力構成:
  note_export/
    month01_副業マインドセット/
      day001.txt
      day002.txt
      ...
    month02_SNS集客/
      ...
    ...
    all_titles.csv   ← タイトル・タグ一覧

各 .txt ファイルの構成:
  ■ タイトル（note のタイトル欄にコピペ）
  ■ タグ（5個、noteのタグ欄にコピペ）
  ■ 本文（noteの本文欄にコピペ）
"""

import csv
import re
import zipfile
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "note_export"
SOURCE_DIR = Path(__file__).parent / "output"


MONTH_NAMES = {
    1:  "副業マインドセットと最初の一歩",
    2:  "SNS集客の基本と発信戦略",
    3:  "コンテンツ作成の型と量産術",
    4:  "Instagram・ショート動画実践運用",
    5:  "商品・サービス設計と価格戦略",
    6:  "セールスライティングと成約率アップ",
    7:  "ファン化・リピーター育成術",
    8:  "自動化・外注・仕組み化",
    9:  "データ分析と改善サイクル",
    10: "ブランディングと差別化戦略",
    11: "スケールアップと収益の拡大",
    12: "1年の総決算と次年度の設計",
}


def parse_md(filepath: Path) -> dict:
    text = filepath.read_text(encoding="utf-8")

    # YAMLフロントマターを取り出す
    meta = {}
    if text.startswith("---"):
        end = text.index("---", 3)
        yaml_block = text[3:end].strip()
        for line in yaml_block.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        body = text[end + 3:].strip()
    else:
        body = text.strip()

    # 本文からタイトル行（# ）を除去
    body = re.sub(r"^#\s+.+\n?", "", body).strip()

    # frontmatterの区切り末尾（---\n#タグ行）を除去
    body = re.sub(r"\n---\n#.+$", "", body).strip()

    return {
        "day":   int(meta.get("day", 0)),
        "month": int(meta.get("month", 0)),
        "title": meta.get("title", ""),
        "theme": meta.get("theme", ""),
        "angle": meta.get("angle", ""),
        "tags":  meta.get("tags", ""),
        "body":  body,
    }


def build_note_text(article: dict) -> str:
    tags_line = "　".join(f"#{t.strip()}" for t in article["tags"].split(","))

    return (
        f"【タイトル】\n"
        f"{article['title']}\n"
        f"\n"
        f"【タグ】\n"
        f"{tags_line}\n"
        f"\n"
        f"{'='*50}\n"
        f"【本文】（以下をnote本文欄にコピペ）\n"
        f"{'='*50}\n"
        f"\n"
        f"{article['body']}\n"
    )


def main():
    md_files = sorted(SOURCE_DIR.glob("day*.md"))
    if not md_files:
        print("output/ に .md ファイルが見つかりません")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    csv_rows = []

    for md_path in md_files:
        article = parse_md(md_path)
        month = article["month"]
        if month == 0:
            continue

        # 月フォルダ
        folder_name = f"month{month:02d}_{MONTH_NAMES.get(month, '')}"
        month_dir = OUTPUT_DIR / folder_name
        month_dir.mkdir(exist_ok=True)

        # 出力ファイル
        out_name = f"day{article['day']:03d}.txt"
        out_path = month_dir / out_name
        out_path.write_text(build_note_text(article), encoding="utf-8")

        csv_rows.append({
            "day":      article["day"],
            "month":    month,
            "filename": f"{folder_name}/{out_name}",
            "title":    article["title"],
            "tags":     article["tags"],
            "theme":    article["theme"],
            "angle":    article["angle"],
        })

    # CSV出力
    csv_path = OUTPUT_DIR / "all_titles.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["day","month","filename","title","tags","theme","angle"])
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"変換完了: {len(csv_rows)} 記事 → {OUTPUT_DIR}/")

    # ZIP化
    zip_path = Path(__file__).parent / "note_import.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in OUTPUT_DIR.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(OUTPUT_DIR.parent))
    print(f"ZIP作成: {zip_path}")
    return zip_path


if __name__ == "__main__":
    main()

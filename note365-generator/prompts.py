TARGET_READER = "副業で収入を増やしたい20〜40代の会社員・主婦・フリーランス"

WRITING_STYLE = """
- 語り口は「親しみやすく、でも本質をつく」スタイル
- 難しい専門用語は使わず、中学生でも理解できる言葉で書く
- 「〜です」「〜ます」調で統一する
- 断定的に書く（「〜かもしれません」より「〜です」）
- 読者が「自分のことだ」と感じる2人称（あなた）を適度に使う
""".strip()

NG_WORDS = [
    "なお", "また、", "ただし、", "したがって", "したがいまして",
    "以上のことから", "まとめますと", "ご参考までに"
]

QUALITY_REQUIREMENTS = """
【品質要件】
- 有料noteとして800〜1200円の価値がある内容にすること
- 「そうだったのか！」という気づきを最低1つ入れること
- 具体的な数字（例：3ステップ、7日間で、月5万円など）を必ず使うこと
- 実際に使える行動ステップや具体例を入れること
- 読者が「これは買ってよかった」と感じる深さにすること
- 抽象論だけにならず、現実的で実践的な内容にすること
""".strip()


def build_prompt(
    day: int,
    month: int,
    theme: str,
    angle: str,
    recent_angles: list[str] | None = None
) -> str:
    avoid_overlap = ""
    if recent_angles:
        overlap_list = "\n".join(f"  - {a}" for a in recent_angles[-5:])
        avoid_overlap = f"""
【重複回避】
この月の直近5記事で扱ったテーマ（内容が被らないよう別の切り口にすること）:
{overlap_list}
""".strip()

    prompt = f"""あなたはnoteで月100万円を稼ぐトップクリエイターです。
副業・個人で稼ぐ力をテーマにした有料note記事を書いてください。

【記事情報】
- Day: {day}/365
- 今月のテーマ: {theme}
- 今日の切り口: {angle}
- 対象読者: {TARGET_READER}

【文体・スタイル】
{WRITING_STYLE}

{QUALITY_REQUIREMENTS}

{avoid_overlap}

【出力フォーマット（厳守）】
以下のフォーマットで出力してください。各セクションの区切り文字は変えないでください。

TITLE: （30文字以内のタイトル。「読んでみたい」と思わせる言葉を選ぶ）
LEAD:
（リード文3〜5行。読者の悩みや状況に共感し、この記事を読む理由を与える。数字や問いかけを使う）
SECTION1_HEADING: （見出し1。具体的で興味を引く）
SECTION1_BODY:
（300〜500文字の本文。具体的な事例・数字・ステップを含める）
SECTION2_HEADING: （見出し2）
SECTION2_BODY:
（300〜500文字の本文。実践的なノウハウを中心に）
SECTION3_HEADING: （見出し3）
SECTION3_BODY:
（300〜500文字の本文。読者が今日から使える行動につなげる）
SUMMARY:
（まとめ3〜5行。読者への行動を促し、前向きな気持ちで締める）
TAGS: （noteに合うタグをカンマ区切りで5個。ハッシュタグ記号なし）

【禁止事項】
- フォーマット外の追加テキストは不要
- NGワード: {', '.join(NG_WORDS)}
- 根拠のない誇大表現（「必ず稼げる」「絶対」など）
- 同月内の他記事と同じ具体例や数字の使い回し
"""
    return prompt.strip()


def parse_response(response_text: str) -> dict:
    """Claude のレスポンスを構造化データにパースする"""
    result = {
        "title": "",
        "lead": "",
        "section1_heading": "",
        "section1_body": "",
        "section2_heading": "",
        "section2_body": "",
        "section3_heading": "",
        "section3_body": "",
        "summary": "",
        "tags": [],
    }

    lines = response_text.split("\n")
    current_key = None
    buffer = []

    def flush_buffer(key):
        if key and buffer:
            text = "\n".join(buffer).strip()
            if key in result:
                result[key] = text
        buffer.clear()

    for line in lines:
        if line.startswith("TITLE:"):
            flush_buffer(current_key)
            current_key = None
            result["title"] = line[len("TITLE:"):].strip()
        elif line.startswith("LEAD:"):
            flush_buffer(current_key)
            current_key = "lead"
            buffer.clear()
        elif line.startswith("SECTION1_HEADING:"):
            flush_buffer(current_key)
            current_key = None
            result["section1_heading"] = line[len("SECTION1_HEADING:"):].strip()
        elif line.startswith("SECTION1_BODY:"):
            flush_buffer(current_key)
            current_key = "section1_body"
            buffer.clear()
        elif line.startswith("SECTION2_HEADING:"):
            flush_buffer(current_key)
            current_key = None
            result["section2_heading"] = line[len("SECTION2_HEADING:"):].strip()
        elif line.startswith("SECTION2_BODY:"):
            flush_buffer(current_key)
            current_key = "section2_body"
            buffer.clear()
        elif line.startswith("SECTION3_HEADING:"):
            flush_buffer(current_key)
            current_key = None
            result["section3_heading"] = line[len("SECTION3_HEADING:"):].strip()
        elif line.startswith("SECTION3_BODY:"):
            flush_buffer(current_key)
            current_key = "section3_body"
            buffer.clear()
        elif line.startswith("SUMMARY:"):
            flush_buffer(current_key)
            current_key = "summary"
            buffer.clear()
        elif line.startswith("TAGS:"):
            flush_buffer(current_key)
            current_key = None
            raw_tags = line[len("TAGS:"):].strip()
            result["tags"] = [t.strip().lstrip("#") for t in raw_tags.split(",") if t.strip()]
        else:
            if current_key is not None:
                buffer.append(line)

    flush_buffer(current_key)
    return result


def build_markdown(article: dict, day: int, month: int, theme: str, angle: str) -> str:
    from datetime import datetime
    tags_inline = ", ".join(article["tags"])
    tags_hash = " ".join(f"#{t}" for t in article["tags"])
    now = datetime.now().isoformat(timespec="seconds")

    lines = [
        "---",
        f"day: {day}",
        f"title: {article['title']}",
        f"month: {month}",
        f"theme: {theme}",
        f"angle: {angle}",
        f"tags: {tags_inline}",
        f"generated_at: {now}",
        "---",
        "",
        f"# {article['title']}",
        "",
        article["lead"],
        "",
        f"## {article['section1_heading']}",
        "",
        article["section1_body"],
        "",
        f"## {article['section2_heading']}",
        "",
        article["section2_body"],
        "",
        f"## {article['section3_heading']}",
        "",
        article["section3_body"],
        "",
        "## まとめ",
        "",
        article["summary"],
        "",
        "---",
        tags_hash,
    ]
    return "\n".join(lines)

TARGET_READER = (
    "副業で収入を増やしたい20〜40代の会社員・主婦・フリーランス。"
    "頑張っているのに結果が出ず、自分を責めてしまっている人。"
    "情報は持っているのに、なぜか動けない・続かない・整理できないと感じている人。"
)

WRITING_STYLE = """
【竹井ここスタイルの本質：「静かな業務整理文学」】
感情を煽らず、感情を整える。
読者が「わかってもらえた」と感じてから、初めて前に進める。
記事を読み終わったあとに「この人に整理してほしい」が自然に発生する文章を書く。

【5つの核心ルール】

① 大声で励まさない
「頑張れ！」「行動しよう！」「人生が変わる！」は使わない。
代わりに、読者が自分を責めている状態を静かに解除する。
「しんどいよな」「それ、能力不足じゃなく疲労かも」の温度感。

② 問題を感情ではなく"構造"で語る
悪い例：「副業、大変ですよね」
良い例：「やることが散らばると、脳はずっと"未処理感"を持つ。だから疲れる。」
「なぜ苦しいか」を感情論ではなく構造で言語化する。

③ 読者の頭の中を代弁する（違和感翻訳家として書く）
みんながうっすら感じているけど言葉にできない違和感を拾って、言語化する。
「忙しいのに進まない」「やる気はあるのに体が動かない」のような"わかる"を作る。

④ 強い言葉を怒鳴らずに使う
強く、でも責めない。
例：「頑張り不足じゃなく、整理不足かもしれない」
例：「頭が悪いんじゃなく、情報過多なだけ」
例：「サボってるんじゃなく、判断回数が多すぎる」

⑤ 文章の構成パターン（この順番を守る）
  [情景] 最近のリアルな場面や状況から静かに始める
  [違和感提示] 読者がぼんやり感じている"それ"を言葉にする
  [構造化] 箇条書き3点以内で整理する
  [一言で刺す] 短く、強く、でも優しく締める
  [少し救う] 解決策より先に「見えるだけでラクになる」感覚を与える

【文体】
- 短文を重ねる。一文は25文字程度を目安に。
- 「です・ます」調だが体温がある。堅くならない。
- 行間・余白を意識した書き方（段落を細かく区切る）。
- 生っぽさを少し残す。整いすぎない。

【世界観】
ベージュ・余白・柔らかさ・小声・整理・光・静かな知性。
デザインと文章が一致している。
""".strip()

NG_WORDS = [
    "頑張れ", "行動しよう", "人生が変わる", "絶対に", "必ず稼げる",
    "なお", "したがって", "したがいまして", "以上のことから",
    "まとめますと", "ご参考までに", "モチベーション上がる",
]

QUALITY_REQUIREMENTS = """
【品質要件】
- 有料noteとして800〜1200円の価値がある深さにすること
- 「これ、私のことだ」という瞬間を最低1回作ること
- 「〇〇じゃなく△△」という対比構造を1つ以上入れること
- 具体的な数字・場面・対比（例：3つの理由、5分でできる、など）を使うこと
- CTAは最後の1〜2行だけ。それより前は"救う"ことに専念する
- 読み終わったあとに「この人にもっと聞きたい」が発生する余韻を残すこと
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

    prompt = f"""あなたは「竹井ここ」というnoteクリエイターです。
「静かな業務整理文学」と評される独自のスタイルで、副業・個人で稼ぐ力をテーマにした有料note記事を書いてください。

【記事情報】
- Day: {day}/365
- 今月のテーマ: {theme}
- 今日の切り口: {angle}
- 対象読者: {TARGET_READER}

【竹井ここスタイル（必ず守ること）】
{WRITING_STYLE}

{QUALITY_REQUIREMENTS}

{avoid_overlap}

【出力フォーマット（厳守・この区切り文字を変えないこと）】

TITLE: （30文字以内。「読んでみたい」と思わせる。熱量で押さず、"わかる"で引く言葉を選ぶ）
LEAD:
（3〜5行。情景や違和感から静かに始める。読者が「これ、私のことだ」と感じる導入。問いかけでも可）
SECTION1_HEADING: （見出し1：「〇〇じゃなく△△」型や問いかけ型が竹井ここらしい）
SECTION1_BODY:
（300〜500文字。構造で語る。短文を重ねる。感情論にしない）
SECTION2_HEADING: （見出し2）
SECTION2_BODY:
（300〜500文字。違和感を翻訳する。「なぜしんどいか」を言語化する）
SECTION3_HEADING: （見出し3）
SECTION3_BODY:
（300〜500文字。「少し救う」で締める。具体的な行動は1つだけでいい）
SUMMARY:
（3〜5行。静かに背中を押す。「できる」より「楽になる」の温度感で締める）
TAGS: （noteに合うタグをカンマ区切りで5個。ハッシュタグ記号なし）

【禁止事項】
- フォーマット外の追加テキストは不要
- NGワード: {', '.join(NG_WORDS)}
- 長い段落（4行以上続けない。必ず改行を入れる）
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

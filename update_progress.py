# -*- coding: utf-8 -*-
"""
update_progress.py (多書卷版 v2.0)

用途：掃描 bible_data 資料夾裡已經產生的 chunks_en_{書卷}_*.json 和
chunks_ja_{書卷}_*.json 檔案，自動算出「每一卷書」哪些章節已標注完成、
哪些還沒，寫成一份 PROGRESS.md，供開新窗口時上傳。

支援多書卷：只要資料夾裡出現任何書卷的批次檔案，這份報告就會自動列出
該書卷的進度，不需要手動指定要追蹤哪幾卷書。

用法（每次存完新的chunks json後，跑一次）：
    python update_progress.py

輸出：
    E:\\bible-lang-app\\bible_data\\PROGRESS.md
"""

import json
import os
import re

BIBLE_DATA_DIR = r"E:\bible-lang-app\bible_data"
BIBLE_TEXT_DIR = os.path.join(BIBLE_DATA_DIR, "bible_text")
PROGRESS_FILE = os.path.join(BIBLE_DATA_DIR, "PROGRESS.md")
BATCH_SIZE = 20

# 檔名裡的書卷代號 → 實際 bible_text 檔名代碼的對照表。
# 詩篇是歷史包袱（批次檔名一開始就用小寫psalms），其餘書卷一律用聖經標準代碼
# （跟 extract_chapter_text.py 的 BOOK 參數保持一致，例如 PRO、MAT）。
BOOK_ALIAS = {"psalms": "PSA"}

PATTERN = re.compile(r"^chunks_(en|ja)_([A-Za-z0-9]+)_(\d{3})-(\d{3})\.json$")


def resolve_book_code(book_slug):
    """把批次檔名裡的書卷代號轉成 bible_text 資料夾裡實際的檔名代碼"""
    return BOOK_ALIAS.get(book_slug, book_slug.upper())


def get_book_info(book_slug):
    """讀取 bible_text/{code}.json，回傳 (總章數, 中文書名)；讀不到則回傳 (None, book_slug)"""
    code = resolve_book_code(book_slug)
    path = os.path.join(BIBLE_TEXT_DIR, f"{code}.json")
    if not os.path.exists(path):
        return None, book_slug
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        total = len(data.get("chapters", {}))
        book_zh = data.get("book_zh", book_slug)
        return total, book_zh
    except Exception:
        return None, book_slug


def scan_ranges():
    """掃描資料夾，回傳 {(lang, book_slug): [(start, end, fname), ...]}"""
    result = {}
    if not os.path.isdir(BIBLE_DATA_DIR):
        return result
    for fname in os.listdir(BIBLE_DATA_DIR):
        m = PATTERN.match(fname)
        if not m:
            continue
        lang, book_slug, start, end = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        key = (lang, book_slug)
        result.setdefault(key, []).append((start, end, fname))
    for key in result:
        result[key].sort()
    return result


def covered_set(ranges):
    s = set()
    for start, end, _ in ranges:
        s.update(range(start, end + 1))
    return s


def compress_to_range_str(covered):
    if not covered:
        return "（尚未開始）"
    nums = sorted(covered)
    parts = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        parts.append(f"{start}" if start == prev else f"{start}-{prev}")
        start = prev = n
    parts.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ", ".join(parts)


def find_first_gap(covered, total):
    if total is None:
        return None
    ch = 1
    while ch <= total:
        if ch not in covered:
            start = ch
            while ch <= total and ch not in covered:
                ch += 1
            return (start, ch - 1)
        ch += 1
    return None


def suggest_next_batch(gap, total, batch_size=BATCH_SIZE):
    if gap is None:
        return None
    start, gap_end = gap
    end = min(start + batch_size - 1, gap_end, total)
    return (start, end)


def count_chunks(ranges):
    total = 0
    for start, end, fname in ranges:
        path = os.path.join(BIBLE_DATA_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            total += len(data)
        except Exception as e:
            print(f"警告：讀取 {fname} 失敗（{e}），計數可能不準。")
    return total


def main():
    ranges_by_key = scan_ranges()

    book_slugs = sorted(set(book for (_, book) in ranges_by_key.keys()))

    if not book_slugs:
        print("目前資料夾裡沒有任何符合格式的批次檔案（chunks_en_{書卷}_###-###.json）。")
        return

    lines = []
    lines.append("# B1 / B2 語塊標注進度追蹤（多書卷版）")
    lines.append("")
    lines.append("（此檔案由 update_progress.py 自動產生，每次做完新一批後重新跑一次即可更新）")
    lines.append("")

    console_summary = []

    for book_slug in book_slugs:
        total_chapters, book_zh = get_book_info(book_slug)
        en_ranges = ranges_by_key.get(("en", book_slug), [])
        ja_ranges = ranges_by_key.get(("ja", book_slug), [])

        en_covered = covered_set(en_ranges)
        ja_covered = covered_set(ja_ranges)

        en_gap = find_first_gap(en_covered, total_chapters)
        ja_gap = find_first_gap(ja_covered, total_chapters)

        en_next = suggest_next_batch(en_gap, total_chapters)
        ja_next = suggest_next_batch(ja_gap, total_chapters)

        en_chunk_total = count_chunks(en_ranges)
        ja_chunk_total = count_chunks(ja_ranges)

        total_str = str(total_chapters) if total_chapters is not None else "未知（找不到bible_text對應檔案）"

        lines.append(f"## {book_zh}（{book_slug}）")
        lines.append("")
        lines.append(f"總章數：{total_str}")
        lines.append("")
        lines.append("### 英文語塊（B1）")
        lines.append(f"- 已完成章節：{compress_to_range_str(en_covered)}")
        lines.append(f"- 已標注語塊總數：{en_chunk_total}")
        if en_next:
            lines.append(f"- **下一批建議範圍：{en_next[0]} ~ {en_next[1]} 章**")
        elif total_chapters is not None:
            lines.append(f"- **全部{total_chapters}章已完成！**")
        lines.append("")
        lines.append("### 日文語塊（B2）")
        lines.append(f"- 已完成章節：{compress_to_range_str(ja_covered)}")
        lines.append(f"- 已標注語塊總數：{ja_chunk_total}")
        if ja_next:
            lines.append(f"- **下一批建議範圍：{ja_next[0]} ~ {ja_next[1]} 章**")
        elif total_chapters is not None:
            lines.append(f"- **全部{total_chapters}章已完成！**")
        lines.append("")

        if en_next and ja_next and en_next == ja_next:
            s, e = en_next
            code = resolve_book_code(book_slug)
            lines.append("下一批建議指令：")
            lines.append("```")
            lines.append(f"python extract_chapter_text.py {code} {s} {e} both")
            lines.append("```")
        else:
            code = resolve_book_code(book_slug)
            if en_next:
                s, e = en_next
                lines.append(f"英文下一批：`python extract_chapter_text.py {code} {s} {e} en`")
            if ja_next:
                s, e = ja_next
                lines.append(f"日文下一批：`python extract_chapter_text.py {code} {s} {e} ja`")

        lines.append("")
        lines.append("---")
        lines.append("")

        console_summary.append(
            f"{book_zh}（{book_slug}）：英文 {compress_to_range_str(en_covered)}（{en_chunk_total}條）"
            f" / 日文 {compress_to_range_str(ja_covered)}（{ja_chunk_total}條）"
        )

    os.makedirs(BIBLE_DATA_DIR, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"進度已更新：{PROGRESS_FILE}")
    print()
    for line in console_summary:
        print(line)


if __name__ == "__main__":
    main()

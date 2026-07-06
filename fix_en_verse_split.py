"""
fix_en_verse_split.py

修復 bible_text/{BOOK}.json 裡英文(WEB譯本)節數合併的bug。

原因：來源HTML在擷取節數時，某些節的文字被黏在前一節的 en 欄位裡，
中間用「節號 + \xa0(不換行空格)」當作沒被正確辨識的節分隔符，
例如：
    "...adultery;' 28\xa0but I tell you..."
其中 "28\xa0" 其實代表第28節的開始，但28節本身的 en 欄位卻是空字串。

用法：
    python fix_en_verse_split.py MRK
    python fix_en_verse_split.py MAT
（不加參數預設 MRK）

執行前會自動備份成 {BOOK}_json.bak（如果備份已存在則不覆蓋，避免誤刪原始備份）。
"""

import json
import re
import shutil
import sys
from pathlib import Path

BOOK = sys.argv[1] if len(sys.argv) > 1 else "MRK"
BIBLE_TEXT_PATH = Path("bible_data") / "bible_text" / f"{BOOK}.json"
BACKUP_PATH = Path("bible_data") / "bible_text" / f"{BOOK}_json.bak"

# 主要模式：數字 + 不換行空格(\xa0)，這是目前已知的bug特徵
PATTERN_XA0 = re.compile(r"\s*(\d{1,3})\xa0")
# 備用模式：句尾標點 + 空白 + 數字 + 空白 + 大寫字母開頭（保險，避免\xa0已被正規化掉的情況）
PATTERN_FALLBACK = re.compile(r"(?<=[.!?’\"”\)])\s+(\d{1,3})\s+(?=[A-Z])")


def split_verse_text(text):
    """回傳 [(None, 本節自己的文字), (目標節號, 該節文字), ...]"""
    matches = list(PATTERN_XA0.finditer(text))
    pattern_used = "xa0"
    if not matches:
        matches = list(PATTERN_FALLBACK.finditer(text))
        pattern_used = "fallback"
    if not matches:
        return None

    segments = []
    first_seg = text[: matches[0].start()].strip()
    segments.append((None, first_seg))
    for i, m in enumerate(matches):
        target_vnum = m.group(1)
        seg_start = m.end()
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        seg_text = text[seg_start:seg_end].strip()
        segments.append((target_vnum, seg_text))
    return segments, pattern_used


def main():
    if not BIBLE_TEXT_PATH.exists():
        print(f"錯誤：找不到 {BIBLE_TEXT_PATH}")
        sys.exit(1)

    if not BACKUP_PATH.exists():
        shutil.copy(BIBLE_TEXT_PATH, BACKUP_PATH)
        print(f"已備份原始檔案至 {BACKUP_PATH}")
    else:
        print(f"備份檔案已存在（{BACKUP_PATH}），不覆蓋")

    with open(BIBLE_TEXT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    fixed_count = 0
    warning_count = 0

    for ch_num, ch_data in data["chapters"].items():
        verses = ch_data["verses"]
        verse_nums = sorted(verses.keys(), key=lambda x: int(x))
        for vnum in verse_nums:
            text = verses[vnum].get("en", "")
            if not text:
                continue
            result = split_verse_text(text)
            if result is None:
                continue
            segments, pattern_used = result

            # 第一段留給自己
            verses[vnum]["en"] = segments[0][1]

            for target_vnum, seg_text in segments[1:]:
                if target_vnum in verses:
                    if verses[target_vnum].get("en"):
                        print(
                            f"警告：第{ch_num}章第{target_vnum}節已有文字，"
                            f"不覆蓋（可能已修復過或有其他問題），略過"
                        )
                        warning_count += 1
                        continue
                    verses[target_vnum]["en"] = seg_text
                    fixed_count += 1
                else:
                    print(
                        f"警告：第{ch_num}章第{target_vnum}節不存在於JSON結構中，"
                        f"文字遺失：{seg_text[:50]}..."
                    )
                    warning_count += 1

    with open(BIBLE_TEXT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n修復完成：共修復 {fixed_count} 節，警告 {warning_count} 件")
    print(f"已存回：{BIBLE_TEXT_PATH}")

    # 修復後檢查：還有沒有空白的en欄位
    empty_verses = []
    for ch_num, ch_data in data["chapters"].items():
        for vnum, v in ch_data["verses"].items():
            if not v.get("en", "").strip():
                empty_verses.append(f"{ch_num}:{vnum}")
    if empty_verses:
        print(f"\n注意：修復後仍有 {len(empty_verses)} 個空白節，前20個：")
        print(empty_verses[:20])
    else:
        print("\n全部節都成功修復，沒有殘留空白節")


if __name__ == "__main__":
    main()

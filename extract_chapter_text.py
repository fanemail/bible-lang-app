# -*- coding: utf-8 -*-
"""
extract_chapter_text.py

用途：從 bible_data/bible_text/{BOOK}.json 擷取指定章節範圍的經文（可選英/中/日），
輸出成純文字檔，供B1（英文）/ B2（日文）語塊標注任務（新窗口）使用。

用法：
    python extract_chapter_text.py START END
        → 預設書卷=PSA、預設語言=en，與原本demo流程相容
    python extract_chapter_text.py BOOK START END
        → 指定書卷代碼，語言預設=en
    python extract_chapter_text.py BOOK START END LANG
        → 指定書卷代碼 + 語言（en / ja / zh）

範例：
    python extract_chapter_text.py 1 10                  (PSA, 英文, 1~10章)
    python extract_chapter_text.py PSA 1 10 ja            (PSA, 日文, 1~10章)
    python extract_chapter_text.py GEN 1 10 zh             (GEN, 中文, 1~10章)

輸出：
    E:\\bible-lang-app\\bible_data\\chunk_task_input_{BOOK}_{LANG}_{START:03d}-{END:03d}.txt
"""

# -*- coding: utf-8 -*-
"""
extract_chapter_text.py

用途：從 bible_data/bible_text/{BOOK}.json 擷取指定章節範圍的經文（英/中/日/英日合併），
輸出成純文字檔，供B1（英文）/ B2（日文）語塊標注任務（新窗口）使用。

用法：
    python extract_chapter_text.py START END
        → 預設書卷=PSA、預設語言=en，與原本demo流程相容
    python extract_chapter_text.py BOOK START END
        → 指定書卷代碼，語言預設=en
    python extract_chapter_text.py BOOK START END LANG
        → 指定書卷代碼 + 語言（en / ja / zh / both）
          LANG=both 會把英文、日文合併成一個檔案，一次上傳給AI即可，
          不用像之前一樣分兩個檔案上傳。

範例：
    python extract_chapter_text.py 1 10                  (PSA, 英文, 1~10章)
    python extract_chapter_text.py PSA 11 30 both          (PSA, 英日合併, 11~30章)  ← 建議用這個
    python extract_chapter_text.py PSA 1 10 ja            (PSA, 日文, 1~10章)
    python extract_chapter_text.py GEN 1 10 zh             (GEN, 中文, 1~10章)

輸出：
    E:\\bible-lang-app\\bible_data\\chunk_task_input_{BOOK}_{LANG}_{START:03d}-{END:03d}.txt
"""

import json
import sys
import os

BIBLE_TEXT_DIR = r"E:\bible-lang-app\bible_data\bible_text"
OUTPUT_DIR = r"E:\bible-lang-app\bible_data"
VALID_LANGS = {"en", "ja", "zh", "both"}


def main():
    args = sys.argv[1:]

    if len(args) == 2:
        book, lang = "PSA", "en"
        start, end = args
    elif len(args) == 3:
        book, start, end = args
        book = book.upper()
        lang = "en"
    elif len(args) == 4:
        book, start, end, lang = args
        book = book.upper()
        lang = lang.lower()
    else:
        print("用法錯誤。")
        print("  python extract_chapter_text.py START END                     (預設書卷=PSA, 語言=en)")
        print("  python extract_chapter_text.py BOOK START END                 (指定書卷, 語言=en)")
        print("  python extract_chapter_text.py BOOK START END LANG            (語言 en/ja/zh/both)")
        sys.exit(1)

    if lang not in VALID_LANGS:
        print(f"錯誤：語言參數必須是 en / ja / zh / both 其中之一，收到的是 '{lang}'")
        sys.exit(1)

    try:
        start, end = int(start), int(end)
    except ValueError:
        print("錯誤：START 和 END 必須是整數章節號。")
        sys.exit(1)

    if start > end:
        print("錯誤：START 不能大於 END。")
        sys.exit(1)

    input_path = os.path.join(BIBLE_TEXT_DIR, f"{book}.json")
    if not os.path.exists(input_path):
        print(f"找不到檔案：{input_path}")
        print("請確認書卷代碼是否正確（應與 bible_text/ 資料夾內的檔名一致）。")
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    book_zh = data.get("book_zh", "")
    chapters = data.get("chapters", {})

    output_lines = []
    verse_count = 0
    chapter_count = 0

    for ch_num in range(start, end + 1):
        ch_key = str(ch_num)
        if ch_key not in chapters:
            print(f"警告：{book} 第{ch_num}章不存在，已跳過。")
            continue

        chapter_count += 1
        verses = chapters[ch_key].get("verses", {})
        output_lines.append(f"\n=== {book} {book_zh} {ch_num} ===\n")

        for v_key in sorted(verses.keys(), key=int):
            if lang == "both":
                en_text = verses[v_key].get("en", "")
                ja_text = verses[v_key].get("ja", "")
                output_lines.append(f"[{ch_num}:{v_key}]")
                output_lines.append(f"  EN: {en_text}")
                output_lines.append(f"  JA: {ja_text}")
            else:
                text = verses[v_key].get(lang, "")
                output_lines.append(f"[{ch_num}:{v_key}] {text}")
            verse_count += 1

    if chapter_count == 0:
        print("錯誤：指定範圍內沒有任何章節資料，未產生檔案。")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f"chunk_task_input_{book}_{lang}_{start:03d}-{end:03d}.txt"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已存檔：{output_path}")
    print(f"（共 {chapter_count} 章、{verse_count} 節）")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
抽查「沒被判定為污染」的詞條，看看 ja 欄位到底是不是真的日文翻譯，
還是其實也是某種佔位/空白/錯誤內容，只是沒被 MyMemory 關鍵字模式抓到而已。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe sample_clean_ja.py
"""
import json
import re

INPUT_PATH = r"E:\bible-lang-app\bible_data\vocab_db.jsonl"
BAD_IDS_PATH = r"E:\bible-lang-app\bible_data\bad_vocab_ids.txt"
SAMPLE_SIZE = 15

def main():
    with open(BAD_IDS_PATH, "r", encoding="utf-8") as f:
        bad_ids = set(line.strip() for line in f if line.strip())

    clean_entries = []
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if item.get("id") not in bad_ids:
                clean_entries.append(item)

    print(f"「未被判定污染」的詞條共 {len(clean_entries)} 條，均勻抽樣 {SAMPLE_SIZE} 條檢視：\n")

    step = max(1, len(clean_entries) // SAMPLE_SIZE)
    shown = 0
    for i in range(0, len(clean_entries), step):
        if shown >= SAMPLE_SIZE:
            break
        item = clean_entries[i]
        print(f"id={item.get('id')}  en={item.get('en')!r}")
        print(f"  ja={item.get('ja')!r}")
        print(f"  zh={item.get('zh')!r}")
        print()
        shown += 1

if __name__ == "__main__":
    main()

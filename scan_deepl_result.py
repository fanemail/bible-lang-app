# -*- coding: utf-8 -*-
"""
掃描 vocab_db_deepl.jsonl（DeepL重查後的新檔案），確認污染是否已清除。
路徑已經改好，直接執行即可，不用自己編輯任何內容。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe scan_deepl_result.py
"""
import json
import re

INPUT_PATH = r"E:\bible-lang-app\bible_data\vocab_db_deepl.jsonl"
OUTPUT_PATH = r"E:\bible-lang-app\bible_data\bad_vocab_ids_deepl.txt"

MYMEMORY_PATTERN = re.compile(r"mymemory|usagelimits|TRANSLATIONS FOR TODAY", re.IGNORECASE)
JAPANESE_CHAR_PATTERN = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]")
LONG_THRESHOLD = 20

def classify(item):
    reasons = []
    en = (item.get("en") or "").strip()
    ja = (item.get("ja") or "").strip()

    if not ja:
        return reasons

    if MYMEMORY_PATTERN.search(ja):
        reasons.append("mymemory_warning")

    if en and ja.lower() == en.lower():
        reasons.append("untranslated")

    if len(ja) > LONG_THRESHOLD:
        reasons.append("suspect_long")

    if not JAPANESE_CHAR_PATTERN.search(ja) and ja.lower() != en.lower():
        reasons.append("no_japanese_chars")

    return reasons

def main():
    total = 0
    empty_ja = 0
    counters = {"mymemory_warning": 0, "untranslated": 0, "suspect_long": 0, "no_japanese_chars": 0}
    samples = {"mymemory_warning": [], "untranslated": [], "suspect_long": [], "no_japanese_chars": []}
    bad_ids = set()

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            item = json.loads(line)
            if not (item.get("ja") or "").strip():
                empty_ja += 1
                continue
            reasons = classify(item)
            if reasons:
                bad_ids.add(item.get("id", "?"))
                for r in reasons:
                    counters[r] += 1
                    if len(samples[r]) < 5:
                        samples[r].append((item.get("id"), item.get("en"), item.get("ja")))

    print(f"檢查檔案：{INPUT_PATH}")
    print(f"總詞條數：{total}")
    print(f"ja為空：{empty_ja}")
    print(f"污染詞條數（聯集，去重）：{len(bad_ids)}（佔全體 {len(bad_ids)/total*100:.1f}%）\n")

    labels = {
        "mymemory_warning": "MyMemory額度警告文字",
        "untranslated": "原詞未翻譯直接複製",
        "suspect_long": f"ja欄位長度超過{LONG_THRESHOLD}字（疑似錯位長段落）",
        "no_japanese_chars": "完全不含日文字元",
    }
    for key, label in labels.items():
        print(f"【{label}】共 {counters[key]} 條")
        for id_, en_, ja_ in samples[key]:
            ja_short = ja_ if len(ja_) <= 40 else ja_[:40] + "..."
            print(f"  {id_} / {en_} → {ja_short!r}")
        print()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for id_ in sorted(bad_ids):
            f.write(id_ + "\n")
    print(f"污染id清單已寫出：{OUTPUT_PATH}")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
掃描 vocab_db.jsonl，找出被翻譯API額度警告訊息污染的詞條
（例如 MyMemory API 免費額度超限時，會把警告句原封不動存進 en/zh/ja/zh_def/ja_def 欄位）。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe scan_bad_vocab.py

輸出：
    - 終端機印出污染條數統計
    - E:\\bible-lang-app\\bible_data\\bad_vocab_ids.txt：污染詞條的id清單（一行一個），
      供之後重新查詢時當作「需要重跑」的清單使用
"""
import json
import re

INPUT_PATH = r"E:\bible-lang-app\bible_data\vocab_db.jsonl"
OUTPUT_PATH = r"E:\bible-lang-app\bible_data\bad_vocab_ids.txt"

BAD_PATTERN = re.compile(r"mymemory|usagelimits|TRANSLATIONS FOR TODAY", re.IGNORECASE)
CHECK_FIELDS = ["en", "zh", "ja", "zh_def", "ja_def"]

def main():
    total = 0
    bad_entries = []
    field_counter = {f: 0 for f in CHECK_FIELDS}

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            item = json.loads(line)
            hit_fields = [f for f in CHECK_FIELDS if item.get(f) and BAD_PATTERN.search(str(item[f]))]
            if hit_fields:
                bad_entries.append((item.get("id", "?"), item.get("en", "?"), hit_fields))
                for f in hit_fields:
                    field_counter[f] += 1

    print(f"總詞條數：{total}")
    print(f"污染詞條數：{len(bad_entries)}（佔 {len(bad_entries)/total*100:.1f}%）")
    print("各欄位污染次數：")
    for f, c in field_counter.items():
        print(f"  {f}: {c}")

    if bad_entries:
        print("\n前20條污染範例（id / en詞 / 受污染欄位）：")
        for id_, en_, fields_ in bad_entries[:20]:
            print(f"  {id_} / {en_} / {fields_}")

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            for id_, en_, fields_ in bad_entries:
                f.write(id_ + "\n")
        print(f"\n完整污染id清單已寫出：{OUTPUT_PATH}")
    else:
        print("沒有發現污染詞條。")

if __name__ == "__main__":
    main()

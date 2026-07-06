# -*- coding: utf-8 -*-
"""
把 vocab_db.jsonl 轉成 vocab_data.js（給 index.html 用 <script src> 載入）。

用法：直接雙擊或在 CMD 執行，不需要參數，路徑已寫死對應你的資料夾結構。
輸入：E:\\bible-lang-app\\bible_data\\vocab_db.jsonl
輸出：E:\\bible-lang-app\\vocab_data.js  （要跟 index.html 放同一個資料夾）
"""
import json

INPUT_PATH = r"E:\bible-lang-app\bible_data\vocab_db.jsonl"
OUTPUT_PATH = r"E:\bible-lang-app\vocab_data.js"

def main():
    entries = []
    skipped = 0
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[警告] 第 {line_num} 行 JSON 解析失敗，已跳過：{e}")
                skipped += 1
                continue
            entries.append(obj)

    print(f"讀取完成：{len(entries)} 條詞條，跳過 {skipped} 條無法解析的行")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("/* 由 build_vocab_data.py 自 vocab_db.jsonl 自動產生，請勿手動編輯 */\n")
        f.write("const VOCAB_DATA = ")
        json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    print(f"已寫出：{OUTPUT_PATH}")
    print("下一步：確認 vocab_data.js 跟 index.html 在同一個資料夾（E:\\bible-lang-app\\），")
    print("然後直接打開 index.html 測試點擊英文單詞。")

if __name__ == "__main__":
    main()

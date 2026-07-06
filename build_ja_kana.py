# -*- coding: utf-8 -*-
"""
用 pykakasi 把 vocab_db.jsonl 裡的日文原詞（ja欄位）轉換出平假名讀音，補上 ja_kana。
不需要API、不需要註冊、不會有額度問題，純本地運算。

安裝依賴（只需一次）：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe -m pip install pykakasi

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe build_ja_kana.py

先自動印出前10條供你肉眼快速確認品質，再繼續處理剩下的7000多條（不需要中途確認，
因為這是離線確定性運算，不像翻譯API有品質不穩定的問題）。
輸出到新檔案 vocab_db_with_kana.jsonl，不覆蓋原始 vocab_db.jsonl。
"""
import json
import pykakasi

INPUT_PATH = r"E:\bible-lang-app\bible_data\vocab_db.jsonl"
OUTPUT_PATH = r"E:\bible-lang-app\bible_data\vocab_db_with_kana.jsonl"

kks = pykakasi.kakasi()

def to_hiragana(text):
    if not text:
        return None
    result = kks.convert(text)
    return "".join(item["hira"] for item in result)

def main():
    entries = []
    with open(INPUT_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    print(f"讀取完成：{len(entries)} 條詞條\n")
    print("=== 前10條轉換結果預覽 ===")
    for item in entries[:10]:
        kana = to_hiragana(item.get("ja"))
        print(f"  {item['en']:15s}  {item.get('ja','')}  ->  {kana}")

    print("\n開始處理全部詞條...")
    updated = 0
    for item in entries:
        kana = to_hiragana(item.get("ja"))
        if kana:
            item["ja_kana"] = kana
            updated += 1

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for item in entries:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n完成：{updated}/{len(entries)} 條補上了假名讀音")
    print(f"輸出檔案：{OUTPUT_PATH}（原始 vocab_db.jsonl 未被覆蓋）")
    print("\n確認前10條預覽沒問題後，執行：")
    print(r'  copy /Y "E:\bible-lang-app\bible_data\vocab_db_with_kana.jsonl" "E:\bible-lang-app\bible_data\vocab_db.jsonl"')
    print("再重新執行 build_vocab_data.py 產生新的 vocab_data.js。")

if __name__ == "__main__":
    main()

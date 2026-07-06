# -*- coding: utf-8 -*-
"""
用剛下載的全本聖經66卷英文文字，對照現有 vocab_db.jsonl 的7042詞，
算出實際覆蓋率，解決「字典範圍到底是詩篇還是全本聖經」的懸念。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe check_vocab_coverage.py
"""
import os
import re
import json
import glob

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
VOCAB_PATH = os.path.join(WORK_DIR, "vocab_db.jsonl")
BIBLE_TEXT_DIR = os.path.join(WORK_DIR, "bible_text")
OUTPUT_PATH = os.path.join(WORK_DIR, "vocab_coverage_missing.txt")

def main():
    # 讀現有字典
    vocab_words = set()
    with open(VOCAB_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                item = json.loads(line)
                vocab_words.add(item["en"].lower())
    print(f"現有字典詞數：{len(vocab_words)}")

    # 從全本聖經66卷文字裡，抽出所有出現過的英文詞（簡單小寫化，不做詞幹化，先看粗略覆蓋率）
    bible_words = set()
    files = glob.glob(os.path.join(BIBLE_TEXT_DIR, "*.json"))
    print(f"讀取到 {len(files)} 卷聖經文字檔案")

    for filepath in files:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        for ch_obj in data["chapters"].values():
            for v in ch_obj["verses"].values():
                en_text = v.get("en", "")
                words = re.findall(r"[a-zA-Z']+", en_text)
                for w in words:
                    bible_words.add(w.lower())

    print(f"全本聖經出現過的不重複英文詞（未詞幹化）：{len(bible_words)}")

    missing = bible_words - vocab_words
    covered = bible_words & vocab_words

    print(f"\n已被字典涵蓋：{len(covered)} 個")
    print(f"字典裡沒有的：{len(missing)} 個")
    print(f"粗略覆蓋率：{len(covered)/len(bible_words)*100:.1f}%")
    print("\n（注意：這是最粗略的估算，沒有做詞幹化，plays/played/playing會被當成3個不同詞，")
    print(" 所以「字典裡沒有的」這個數字會偏高估，實際詞幹化後的真實缺口會比這個數字小。）")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for w in sorted(missing):
            f.write(w + "\n")
    print(f"\n缺少的詞清單已寫出：{OUTPUT_PATH}")

if __name__ == "__main__":
    main()

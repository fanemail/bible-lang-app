# -*- coding: utf-8 -*-
"""
檢查 vocab_list.json 的實際詞數，並跟 vocab_db.jsonl 已完成的7042條比對，
確認是否只是「查詢階段(step2)沒跑完」，而不是「詞彙清單本身範圍不夠」。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe check_vocab_list_status.py
"""
import os
import json

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
VOCAB_LIST_PATH = os.path.join(WORK_DIR, "vocab_list.json")
VOCAB_DB_PATH = os.path.join(WORK_DIR, "vocab_db.jsonl")

def main():
    if not os.path.exists(VOCAB_LIST_PATH):
        print(f"找不到 {VOCAB_LIST_PATH}")
        return

    with open(VOCAB_LIST_PATH, encoding="utf-8") as f:
        vocab_list = json.load(f)
    print(f"vocab_list.json 總詞數：{len(vocab_list)}")

    done_words = set()
    if os.path.exists(VOCAB_DB_PATH):
        with open(VOCAB_DB_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    item = json.loads(line)
                    done_words.add(item["en"])
    print(f"vocab_db.jsonl 已完成查詢：{len(done_words)}")

    remaining = [w for w in vocab_list if w not in done_words]
    print(f"\n尚未查詢的詞數：{len(remaining)}")
    if remaining:
        print(f"前20個範例：{remaining[:20]}")
        print("\n【結論】vocab_list.json 早就是完整範圍了，只是 step2（查詢翻譯）沒跑完，")
        print("接著跑完 step2 即可，不需要重新抽詞。")
    else:
        print("\n【結論】vocab_list.json 裡的詞全部都已經查完了，7042就是這份清單的全部，")
        print("如果還有缺口，缺口是出在 vocab_list.json 本身涵蓋範圍不夠（可能是nltk沒正常載入，")
        print("退回了簡易規則），需要另外處理。")

if __name__ == "__main__":
    main()

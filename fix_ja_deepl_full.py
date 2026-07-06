# -*- coding: utf-8 -*-
"""
用 DeepL API 全面重新查詢 vocab_db.jsonl 裡全部 7042 條的 ja 欄位
（不只修污染的4325條，全部重查，確保整本詞典來源、風格一致）。

安全設計：
  - 批次查詢（每批50個詞），比逐字查詢快很多，7042條大約幾分鐘內能跑完
  - 每批查完立刻寫入checkpoint檔案，可中斷、可重新執行自動接續
  - 不覆蓋原始 vocab_db.jsonl，最終結果寫到新檔案，你確認沒問題後手動替換

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe fix_ja_deepl_full.py
"""
import os
import json
import time
import requests

API_KEY = "3ea148d0-5067-402a-b6e4-374c72452a4b:fx"
API_URL = "https://api-free.deepl.com/v2/translate"  # Free版金鑰必須用 api-free 這個domain

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
VOCAB_PATH = os.path.join(WORK_DIR, "vocab_db.jsonl")
CHECKPOINT_PATH = os.path.join(WORK_DIR, "ja_deepl_checkpoint.jsonl")
FAILED_LOG = os.path.join(WORK_DIR, "ja_deepl_failed.txt")
OUTPUT_PATH = os.path.join(WORK_DIR, "vocab_db_deepl.jsonl")  # 不覆蓋原始檔

BATCH_SIZE = 50
DELAY_BETWEEN_BATCHES = 0.4
RETRY_COUNT = 3


def load_vocab():
    entries = []
    with open(VOCAB_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def load_checkpoint():
    """讀取已完成的id集合，用來跳過（斷點續查的關鍵）"""
    done = {}
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    done[item['id']] = item['ja']
                except json.JSONDecodeError:
                    continue
    return done


def translate_batch(words):
    headers = {"Authorization": f"DeepL-Auth-Key {API_KEY}"}
    data = [("text", w) for w in words] + [("target_lang", "JA"), ("source_lang", "EN")]
    for attempt in range(RETRY_COUNT):
        try:
            resp = requests.post(API_URL, headers=headers, data=data, timeout=20)
            if resp.status_code == 200:
                result = resp.json()
                return [t["text"] for t in result["translations"]]
            elif resp.status_code == 456:
                print("【嚴重】已超出DeepL每月免費額度限制，停止執行。")
                return None
            else:
                print(f"  [HTTP {resp.status_code}] 第{attempt+1}次重試...")
                time.sleep(2 * (attempt + 1))
        except Exception as e:
            print(f"  [連線錯誤] 第{attempt+1}次重試：{e}")
            time.sleep(2 * (attempt + 1))
    return None  # 這個batch全部重試失敗


def main():
    entries = load_vocab()
    print(f"詞典總條數：{len(entries)}")

    done = load_checkpoint()
    print(f"已從checkpoint恢復：{len(done)} 條")

    todo = [e for e in entries if e['id'] not in done]
    print(f"本次還需查詢：{len(todo)} 條\n")

    if not todo:
        print("全部查完了，直接跳到最後合併步驟。")
    else:
        checkpoint_f = open(CHECKPOINT_PATH, 'a', encoding='utf-8')
        fail_f = open(FAILED_LOG, 'a', encoding='utf-8')

        batches = [todo[i:i + BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
        for b_idx, batch in enumerate(batches, 1):
            words = [e['en'] for e in batch]
            translations = translate_batch(words)

            if translations is None:
                for e in batch:
                    fail_f.write(e['id'] + "\t" + e['en'] + "\n")
                fail_f.flush()
                print(f"[批次 {b_idx}/{len(batches)}] 失敗，已記錄到 {FAILED_LOG}，跳過")
            else:
                for e, ja in zip(batch, translations):
                    checkpoint_f.write(json.dumps({"id": e['id'], "en": e['en'], "ja": ja}, ensure_ascii=False) + "\n")
                checkpoint_f.flush()
                print(f"[批次 {b_idx}/{len(batches)}] 完成 {len(batch)} 條（累計 {len(done) + b_idx * BATCH_SIZE}/{len(entries)}）")

            time.sleep(DELAY_BETWEEN_BATCHES)

        checkpoint_f.close()
        fail_f.close()
        print("\n本輪查詢結束。")

    # ===== 合併步驟：把checkpoint套用回vocab_db，輸出新檔案 =====
    done = load_checkpoint()  # 重新讀一次，含這輪剛查完的
    fixed_count = 0
    for item in entries:
        if item['id'] in done:
            item['ja'] = done[item['id']]
            fixed_count += 1

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for item in entries:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"已套用 {fixed_count}/{len(entries)} 條ja欄位，寫出新檔案：{OUTPUT_PATH}")
    if fixed_count < len(entries):
        print(f"還有 {len(entries) - fixed_count} 條未完成（可能查詢失敗），直接重新執行本腳本會自動接續。")
    else:
        print("全部完成！確認內容沒問題後，把 vocab_db_deepl.jsonl 改名蓋掉 vocab_db.jsonl，")
        print("再重新執行 build_vocab_data.py 產生新的 vocab_data.js。")


if __name__ == "__main__":
    main()

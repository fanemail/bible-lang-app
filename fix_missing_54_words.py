# -*- coding: utf-8 -*-
"""
補齊字典缺少的54個詞根，沿用整條已驗證的流程：
  - en_ipa/zh/zh_def：有道免費接口（跟step2、跟原本7042條同一個來源）
  - ja：DeepL API（跟之前重查7042條ja欄位同一個來源，穩定乾淨）
  - zh_py：pypinyin（本機運算）
  - ja_kana：pykakasi（本機運算，跟build_ja_kana.py同邏輯）

輸出到新檔案 vocab_db_supplement.jsonl，不直接動 vocab_db.jsonl，
你看過內容沒問題後，再用檔案結尾印出的指令合併。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe fix_missing_54_words.py

需要套件：requests, pykakasi, pypinyin（pypinyin這次是第一次用，需要先裝）
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe -m pip install pypinyin
"""
import os
import re
import json
import time
import requests
import pykakasi
from pypinyin import pinyin, Style

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
MISSING_PATH = os.path.join(WORK_DIR, "vocab_coverage_missing_v2.txt")
VOCAB_DB_PATH = os.path.join(WORK_DIR, "vocab_db.jsonl")
OUTPUT_PATH = os.path.join(WORK_DIR, "vocab_db_supplement.jsonl")

DEEPL_API_KEY = "3ea148d0-5067-402a-b6e4-374c72452a4b:fx"
DEEPL_URL = "https://api-free.deepl.com/v2/translate"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

kks = pykakasi.kakasi()


def to_hiragana(text):
    if not text:
        return None
    result = kks.convert(text)
    return "".join(item["hira"] for item in result)


def to_pinyin(text):
    if not text:
        return None
    return " ".join(p[0] for p in pinyin(text, style=Style.TONE))


def query_youdao_zh(word):
    url = f"https://dict.youdao.com/jsonapi?q={word}"
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            data = resp.json()
            ec = data.get("ec", {}).get("word", [])
            if not ec:
                return None
            entry = ec[0] if isinstance(ec, list) else ec
            us_phone = entry.get("usphone", "")
            trs = entry.get("trs", [])
            zh_defs, zh_core_words = [], []
            for tr in trs:
                pos_info = tr.get("tr", [{}])[0].get("l", {}).get("i", [])
                for item in pos_info:
                    zh_defs.append(item)
                    core = re.sub(r'^[a-zA-Z]+\.\s*', '', item)
                    core = re.split(r'[（(；;，,]', core)[0].strip()
                    if core:
                        zh_core_words.append(core)
            return {
                "en_ipa": us_phone,
                "zh_def": "；".join(zh_defs[:3]) if zh_defs else None,
                "zh_word": zh_core_words[0] if zh_core_words else None,
            }
        except Exception:
            time.sleep(0.5)
    return None


def query_deepl_ja(word):
    headers = {"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"}
    data = [("text", word), ("target_lang", "JA"), ("source_lang", "EN")]
    try:
        resp = requests.post(DEEPL_URL, headers=headers, data=data, timeout=15)
        if resp.status_code == 200:
            return resp.json()["translations"][0]["text"]
    except Exception:
        pass
    return None


def get_next_id(existing_ids):
    nums = [int(i[1:]) for i in existing_ids if i.startswith("V") and i[1:].isdigit()]
    return max(nums) + 1 if nums else 1


def main():
    with open(MISSING_PATH, encoding="utf-8") as f:
        missing_words = [line.strip() for line in f if line.strip()]
    print(f"待補詞數：{len(missing_words)}")

    existing_ids = set()
    with open(VOCAB_DB_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                existing_ids.add(json.loads(line)["id"])
    next_id = get_next_id(existing_ids)

    results = []
    for i, word in enumerate(missing_words, 1):
        zh_result = query_youdao_zh(word) or {}
        ja_raw = query_deepl_ja(word)

        entry = {
            "id": f"V{next_id:05d}",
            "en": word,
            "en_ipa": zh_result.get("en_ipa"),
            "zh": zh_result.get("zh_word"),
            "zh_py": to_pinyin(zh_result.get("zh_word")),
            "zh_def": zh_result.get("zh_def"),
            "ja": ja_raw,
            "ja_kana": to_hiragana(ja_raw),
            "ja_def": None,
            "freq": None,
        }
        results.append(entry)
        next_id += 1
        print(f"[{i}/{len(missing_words)}] {word} -> zh={entry['zh']} / ja={entry['ja']}")
        time.sleep(0.3)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for entry in results:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\n完成，已寫出：{OUTPUT_PATH}（{len(results)}條，尚未合併進主字典）")
    print("看過內容沒問題後，執行以下指令合併進主字典：")
    print(f'  type "{OUTPUT_PATH}" >> "{VOCAB_DB_PATH}"')
    print("合併後記得重新執行 build_vocab_data.py 產生新的 vocab_data.js。")


if __name__ == "__main__":
    main()

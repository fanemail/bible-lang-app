# -*- coding: utf-8 -*-
"""
階段二：逐詞查詢辭典API，建立三語詞彙資料庫（可斷點續查）
========================================================
讀取 step1 產出的 vocab_list.json，對每個詞查詢：
  - 英文IPA音標 + 中文釋義（有道字典 jsonapi）
  - 日文翻譯（MyMemory免費翻譯API，機器翻譯草稿，之後可人工/AI複審）

【誠實說明，執行前務必先看】
- 中文部分（有道jsonapi）是你們之前Collins App用過的同一個來源模式，方法本身有先例，
  但確切的JSON結構有可能隨時間改版，我沒辦法在這裡先幫你連網測試過。
- 日文部分，全景文檔裡沒有明確指定固定來源，這裡先用MyMemory這個不需要金鑰、
  不需要簽名參數的免費機器翻譯API頂著，品質是機器翻譯等級，之後建議像你們
  Collins App的流程一樣，批次拿去給AI複審修正，不要直接當最終版使用。
- 讀音假名（ja_kana）、拼音（zh_py）這次沒有一併產生，留白，
  這兩個屬於「單詞的注音」，可以之後另外用工具批次補上。

【強烈建議】
先只跑前5～10個詞試一次，打開輸出檔案看看結果像不像樣，
確認沒問題再放著跑一整夜，不要沒測過就直接long-run。

每查完一個詞就立刻寫入一行（JSON Lines格式），中斷、跳電、重開機都沒關係，
重新執行同一支腳本，會自動跳過已經查過的詞，接著查沒查過的。

執行方式（Windows CMD）：
"C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" step2_build_vocab_db.py

需要先安裝套件（只需跑一次）：
"C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" -m pip install requests
"""

import os
import re
import json
import time
import requests

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
VOCAB_LIST_PATH = os.path.join(WORK_DIR, "vocab_list.json")
OUTPUT_JSONL = os.path.join(WORK_DIR, "vocab_db.jsonl")
FAILED_LOG = os.path.join(WORK_DIR, "vocab_failed.txt")

REQUEST_TIMEOUT = 8
RETRY_COUNT = 2
SLEEP_BETWEEN = 0.3  # 每個詞查完稍微停頓，避免請求過於密集

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def load_vocab_list():
    with open(VOCAB_LIST_PATH, encoding='utf-8') as f:
        return json.load(f)


def load_done_words():
    """讀取已經查過的詞（斷點續查的關鍵）"""
    done = set()
    if os.path.exists(OUTPUT_JSONL):
        with open(OUTPUT_JSONL, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    done.add(entry.get("en"))
                except json.JSONDecodeError:
                    continue
    return done


def query_youdao_zh(word):
    """查有道字典 jsonapi，取英文IPA + 中文釋義。結構若改版需要調整這裡的解析。"""
    url = f"https://dict.youdao.com/jsonapi?q={word}"
    for attempt in range(RETRY_COUNT + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            data = resp.json()
            ec = data.get("ec", {}).get("word", [])
            if not ec:
                return None
            entry = ec[0] if isinstance(ec, list) else ec
            us_phone = entry.get("usphone", "")
            trs = entry.get("trs", [])
            zh_defs = []       # 完整釋義句，含詞性標記，放zh_def
            zh_core_words = [] # 乾淨的中文詞本身，放zh
            for tr in trs:
                pos_info = tr.get("tr", [{}])[0].get("l", {}).get("i", [])
                for item in pos_info:
                    zh_defs.append(item)
                    # 把"n. 亚伦（男子名）；亚伦（摩西之兄...）"這種完整句子，
                    # 去掉詞性標記(n./v./adj.等)和括號註解，取第一個乾淨的詞當zh
                    core = re.sub(r'^[a-zA-Z]+\.\s*', '', item)  # 去掉開頭詞性標記
                    core = re.split(r'[（(；;，,]', core)[0].strip()  # 只取第一個分號/括號前的部分
                    if core:
                        zh_core_words.append(core)
            zh_def = "；".join(zh_defs[:3]) if zh_defs else None
            zh_word = zh_core_words[0] if zh_core_words else None
            return {
                "en_ipa": us_phone,
                "zh_def": zh_def,
                "zh_word": zh_word,
            }
        except Exception:
            time.sleep(0.5)
    return None


def query_ja_translate(word):
    """MyMemory免費機器翻譯API，做日文草稿翻譯，之後建議人工/AI複審。"""
    url = "https://api.mymemory.translated.net/get"
    params = {"q": word, "langpair": "en|ja"}
    for attempt in range(RETRY_COUNT + 1):
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            data = resp.json()
            translated = data.get("responseData", {}).get("translatedText")
            if translated:
                # 去除機器翻譯常見的多餘標點雜訊（驚嘆號、問號、句號等）
                translated = translated.strip().strip("！？!?。.、,，")
            return translated
        except Exception:
            time.sleep(0.5)
    return None


def build_entry(word, idx):
    zh_result = query_youdao_zh(word) or {}
    ja_result = query_ja_translate(word)

    entry = {
        "id": f"V{idx:05d}",
        "en": word,
        "en_ipa": zh_result.get("en_ipa"),
        "zh": zh_result.get("zh_word"),
        "zh_py": None,           # 待補：拼音
        "zh_def": zh_result.get("zh_def"),
        "ja": ja_result,         # 機器翻譯草稿，待複審
        "ja_kana": None,         # 待補：假名讀音
        "ja_def": None,          # 待補：日文釋義（目前只有翻譯詞，沒有解釋句）
        "freq": None,            # 待補：COCA詞頻（來源尚未確認，全景文檔待確認事項）
    }
    return entry


def main():
    vocab_list = load_vocab_list()
    done_words = load_done_words()
    todo = [w for w in vocab_list if w not in done_words]

    print(f"詞彙總數：{len(vocab_list)}，已完成：{len(done_words)}，待查：{len(todo)}")
    if not todo:
        print("全部查完了！")
        return

    with open(OUTPUT_JSONL, 'a', encoding='utf-8') as out_f, \
         open(FAILED_LOG, 'a', encoding='utf-8') as fail_f:

        for n, word in enumerate(todo, 1):
            idx = len(done_words) + n
            try:
                entry = build_entry(word, idx)
                out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                out_f.flush()
            except Exception as e:
                fail_f.write(f"{word}\t{e}\n")
                fail_f.flush()

            if n % 50 == 0 or n == len(todo):
                print(f"進度：{n}/{len(todo)}（累計完成 {len(done_words)+n}/{len(vocab_list)}）")

            time.sleep(SLEEP_BETWEEN)

    print("本輪執行完畢。若中途中斷過，重新執行本腳本會自動接著查剩下的詞。")


if __name__ == "__main__":
    main()

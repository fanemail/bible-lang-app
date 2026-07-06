# -*- coding: utf-8 -*-
"""
diagnose_mat_split.py

用途：對照 fix_mat_en_split.py 執行後印出的「無法自動修復」清單，
從備份檔案 MAT.json.bak（修復前的原始資料）裡，把這些卡住的段落的
原始英文全文抓出來，方便判斷是什麼樣式沒被正則表達式抓到。

用法：
    1. 把下面 PROBLEM_SPOTS 換成 fix_mat_en_split.py 印出的清單
       （已經預填好你這次執行的結果，不用改）
    2. python diagnose_mat_split.py
    3. 把畫面輸出全部複製貼給 Claude

輸出：對每個問題章節，印出「這個run起點所在節」的原始英文全文，
以及這個run理論上應該涵蓋哪些節號。
"""

import json

BACKUP_PATH = r"E:\bible-lang-app\bible_data\bible_text\MAT.json.bak"

# 從 fix_mat_en_split.py 的輸出貼過來的清單：{章: [卡住的節號, ...]}
PROBLEM_SPOTS = {
    "3": [12],
    "5": [28, 30, 32, 34, 39, 44],
    "8": [13, 16],
    "9": [30, 31],
    "10": [37],
    "11": [6, 11, 13],
    "12": [5, 13, 49],
    "13": [51, 56],
    "14": [19, 26, 32],
    "15": [5],
    "16": [20],
    "17": [13, 18],
    "18": [17, 25],
    "19": [5, 6, 15, 22],
    "20": [9],
    "22": [38, 40],
    "23": [15, 26, 34],
    "24": [30, 37],
    "25": [8],
    "26": [27, 32, 37],
    "27": [36, 46],
}


def main():
    with open(BACKUP_PATH, encoding="utf-8") as f:
        data = json.load(f)

    for ch_key, missing_nums in PROBLEM_SPOTS.items():
        ch_data = data["chapters"].get(ch_key)
        if not ch_data:
            print(f"=== 第{ch_key}章：找不到這一章的資料 ===\n")
            continue
        verses = ch_data["verses"]
        verse_nums = sorted(int(v) for v in verses.keys())

        # 找出每個missing_num所屬的run：往前找最近一個英文非空的節，
        # 那就是這個run實際的起點（合併文字的來源節）
        missing_set = set(missing_nums)
        reported_starts = set()
        for mnum in missing_nums:
            start = mnum
            while start - 1 in verse_nums and not verses[str(start - 1)].get("en", "").strip():
                start -= 1
            # 再往前一格，找到真正有內容的起點
            origin = start - 1
            if origin in reported_starts:
                continue
            reported_starts.add(origin)

            if origin < 1 or str(origin) not in verses:
                print(f"=== 第{ch_key}章 節{mnum} 附近：找不到起點節 ===\n")
                continue

            origin_text = verses[str(origin)].get("en", "")
            print(f"=== 第{ch_key}章 節{origin}（起點）的原始英文全文 ===")
            print(origin_text)
            print()

    print("=== 診斷輸出結束，請把以上全部內容複製貼給 Claude ===")


if __name__ == "__main__":
    main()

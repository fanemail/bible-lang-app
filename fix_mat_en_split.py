# -*- coding: utf-8 -*-
"""
fix_mat_en_split.py

用途：修復 bible_text/MAT.json 裡英文(WEB譯本)節數切分錯誤的問題。

現象：某些節的英文文字是好幾節黏在一起的長段落，內嵌著下一節的節號
（例如 "...Isaac became the father of Jacob.   3 Judah became..."），
而這些節號實際切分後應該分到的節，英文欄位卻是空字串。日文欄位沒有這個問題。

修復邏輯：
1. 掃描每一章，找出「英文有內容、但緊接著連續幾節英文是空字串」的情況
2. 用正則表達式在該節英文文字裡找出內嵌的節號標記
   （樣式：兩個以上空格 + 數字 + 空格 + 大寫字母或引號開頭）
3. 依內嵌節號位置切開文字，分配回正確的節
4. 找不到對應內嵌節號、無法完全還原的情況，保留原樣並在報告中列出節號，
   供人工檢查（不會硬套錯誤的切分導致資料更爛）

用法：
    python fix_mat_en_split.py

會先備份原始檔案為 MAT.json.bak，再覆蓋寫入修復後的 MAT.json。
如果之後在其他書卷（路加、約翰等）發現一樣的問題，把這支腳本的
BIBLE_TEXT_PATH 改成對應書卷的檔案路徑即可重複使用。
"""

import json
import os
import re
import shutil

BIBLE_TEXT_PATH = r"E:\bible-lang-app\bible_data\bible_text\MAT.json"
BACKUP_PATH = BIBLE_TEXT_PATH + ".bak"

# 抓取內嵌節號的樣式：一個以上空格 + 1~3位數字 + 空格 + 英文字母或引號開頭
# （原始WEB文字的分隔空格數量不統一，有時1個、有時2~3個都有；
#  真正的安全機制是後面 split_merged_verse() 裡「節號必須落在預期節號清單內
#  且遞增」的驗證，不是靠空格數量把關）
SPLIT_PATTERN = re.compile(r'\s+(\d{1,3})\s+(?=[A-Za-z"\u2018\u201c\u2019])')


def split_merged_verse(text, expected_verse_nums):
    """
    嘗試把一段合併文字，依內嵌節號切分成 {節號: 文字} 的字典。

    expected_verse_nums：這段文字理論上應該涵蓋的節號清單（遞增排序），
    第一個是這段文字本身所在的節號，其餘是後面緊接著英文為空的節號。

    回傳 (切分結果字典, 是否完全成功涵蓋所有expected節號)
    """
    matches = list(SPLIT_PATTERN.finditer(text))

    valid_splits = []
    expected_set = set(expected_verse_nums[1:])
    last_num = expected_verse_nums[0]
    for m in matches:
        num = int(m.group(1))
        if num in expected_set and num > last_num:
            valid_splits.append((num, m.start(), m.end()))
            last_num = num

    if not valid_splits:
        return {expected_verse_nums[0]: text.strip()}, (len(expected_verse_nums) == 1)

    result = {}
    first_num = expected_verse_nums[0]
    result[first_num] = text[:valid_splits[0][1]].strip()

    for i, (num, start, end) in enumerate(valid_splits):
        seg_start = end
        seg_end = valid_splits[i + 1][1] if i + 1 < len(valid_splits) else len(text)
        result[num] = text[seg_start:seg_end].strip()

    success = set(result.keys()) == set(expected_verse_nums)
    return result, success


def fix_chapter(verses):
    """
    修復單一章節的verses字典（{節號字串: {"en":..., "ja":..., ...}}）。
    直接原地修改傳入的verses字典。
    回傳 (補上內容的節數, 無法自動修復的節號清單)
    """
    verse_nums = sorted(int(v) for v in verses.keys())
    fixed_count = 0
    unresolved = []

    i = 0
    while i < len(verse_nums):
        vnum = verse_nums[i]
        vkey = str(vnum)
        en_text = verses[vkey].get("en", "")

        if en_text.strip():
            run = [vnum]
            j = i + 1
            while j < len(verse_nums):
                next_vnum = verse_nums[j]
                next_key = str(next_vnum)
                next_en = verses[next_key].get("en", "")
                if not next_en.strip():
                    run.append(next_vnum)
                    j += 1
                else:
                    break

            if len(run) > 1:
                split_result, success = split_merged_verse(en_text, run)
                for num, seg_text in split_result.items():
                    verses[str(num)]["en"] = seg_text
                fixed_count += len(split_result) - 1
                if not success:
                    missing = set(run) - set(split_result.keys())
                    unresolved.extend(sorted(missing))
            i = j
        else:
            i += 1

    return fixed_count, unresolved


def main():
    if not os.path.exists(BIBLE_TEXT_PATH):
        print(f"找不到檔案：{BIBLE_TEXT_PATH}")
        return

    shutil.copy2(BIBLE_TEXT_PATH, BACKUP_PATH)
    print(f"已備份原始檔案至：{BACKUP_PATH}")

    with open(BIBLE_TEXT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    total_fixed = 0
    total_unresolved = []

    for ch_key, ch_data in data.get("chapters", {}).items():
        verses = ch_data.get("verses", {})
        fixed_count, unresolved = fix_chapter(verses)
        total_fixed += fixed_count
        if unresolved:
            total_unresolved.append((ch_key, unresolved))

    with open(BIBLE_TEXT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"修復完成，共補上 {total_fixed} 節的英文內容。")
    if total_unresolved:
        print("以下章節有節號無法自動修復（英文欄位仍為空，建議人工檢查原始WEB經文）：")
        for ch_key, missing in total_unresolved:
            print(f"  第{ch_key}章：節 {missing}")
    else:
        print("所有節都成功修復，沒有殘留空白節。")


if __name__ == "__main__":
    main()

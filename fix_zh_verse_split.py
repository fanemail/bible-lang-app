# -*- coding: utf-8 -*-
"""
中文經文「多節被合併成一節」修復腳本。

背景：download_bible_full.py下載中文（cmn-cu89t）經文時，解析邏輯假設「每一節
都有獨立的HTML節號標記」，但中文來源網頁的實際結構是：每個段落只有第一節有
HTML標記，段落內後續的節號是直接寫在段落文字裡的純文字（例如「...非常混沌。
2　地是空虛混沌...」，這個「2」只是文字，不是HTML標記）。原本的解析邏輯認不出
這種純文字節號，導致段落裡除了第一節以外的其他節文字全部被吞併進第一節，
其餘節變成空的。英文、日文來源網頁結構不同，不受影響。

本腳本原理：偵測中文文字裡「數字＋不斷行空格（U+00A0）」這種內嵌節號標記
（這是網頁排版遺留下來、肉眼不容易發現的特殊空格字元，一般文字不會用到這種
搭配，家譜章節裡的年齡數字用的是「九百三十歲」這種中文數字寫法，不會誤判），
把文字依標記切開，分別歸還給正確的節。

用法（3.14主環境，不需要whisperx_env）：
  python fix_zh_verse_split.py
會自動掃描 bible_data/bible_text/ 底下所有書卷json檔案並修復，
修復前會先把原始檔案備份到 bible_data/bible_text_backup_before_zh_fix/，
修復完成後記得重跑 build_book_text_data.py 重新產生 {代碼}_data.js。
"""
import os, re, json, shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIBLE_TEXT_DIR = os.path.join(BASE_DIR, "bible_data", "bible_text")
BACKUP_DIR = os.path.join(BASE_DIR, "bible_data", "bible_text_backup_before_zh_fix")

# 內嵌節號標記：1~3位數字緊接不斷行空格(U+00A0)。中文經文本身用的是中文數字
# （九百三十歲、一百八十七歲…），不會有「阿拉伯數字＋不斷行空格」這種搭配，
# 所以這個pattern只會命中真正的節號標記，不會誤判家譜年齡等內容。
MARKER_RE = re.compile(r'(\d{1,3})\xa0')


def split_merged_zh(chapter_verses):
    """修正單一章節：把被合併進前一節的中文文字，依內嵌節號標記拆回正確節。
       回傳(修復節數, 無法歸位的標記清單)。"""
    verse_nums_sorted = sorted(chapter_verses.keys(), key=int)
    fixed_count = 0
    unresolved = []
    for vn in verse_nums_sorted:
        zh = chapter_verses[vn].get("zh", "")
        if not zh:
            continue
        matches = list(MARKER_RE.finditer(zh))
        if not matches:
            continue
        segments = []
        cursor = 0
        owner = vn
        for m in matches:
            segments.append((owner, zh[cursor:m.start()].strip()))
            owner = m.group(1)
            cursor = m.end()
        segments.append((owner, zh[cursor:].strip()))

        for owner_vn, text in segments:
            if owner_vn not in chapter_verses:
                # 標記到的節號在這章裡不存在（理論上不該發生，保險起見跳過並記錄）
                unresolved.append((vn, owner_vn))
                continue
            if owner_vn == vn:
                chapter_verses[vn]["zh"] = text
            else:
                # 只在目標節目前為空時才填入，不覆蓋已有內容，避免重複執行本腳本時出錯
                if not chapter_verses[owner_vn].get("zh"):
                    chapter_verses[owner_vn]["zh"] = text
                    fixed_count += 1
    return fixed_count, unresolved


def main():
    if not os.path.isdir(BIBLE_TEXT_DIR):
        print(f"!! 找不到 {BIBLE_TEXT_DIR}")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)

    total_fixed = 0
    total_unresolved = 0
    book_reports = []

    for fname in sorted(os.listdir(BIBLE_TEXT_DIR)):
        if not fname.endswith(".json"):
            continue
        src_path = os.path.join(BIBLE_TEXT_DIR, fname)

        with open(src_path, encoding="utf-8") as f:
            data = json.load(f)

        book_fixed = 0
        book_unresolved = []
        for ch_obj in data.get("chapters", {}).values():
            n, unresolved = split_merged_zh(ch_obj["verses"])
            book_fixed += n
            book_unresolved.extend(unresolved)

        if book_fixed == 0 and not book_unresolved:
            continue  # 這卷完全沒有受影響，跳過（不用備份、不用重寫）

        # 備份原始檔案（只在真的有改動時才備份，避免沒問題的書卷也產生備份檔）
        shutil.copy2(src_path, os.path.join(BACKUP_DIR, fname))

        with open(src_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        total_fixed += book_fixed
        total_unresolved += len(book_unresolved)
        book_reports.append((fname, book_fixed, book_unresolved))
        print(f"{fname}：修復{book_fixed}節" + (f"，{len(book_unresolved)}個標記無法歸位" if book_unresolved else ""))

    print(f"\n{'='*50}")
    print(f"總計修復{total_fixed}節，{total_unresolved}個標記無法歸位（需人工核對）")
    print(f"原始檔案已備份到：{BACKUP_DIR}")
    if not book_reports:
        print("沒有任何書卷受影響（可能已經修過，或這批資料本身沒有這個問題）。")
    else:
        print("\n下一步：重新執行 build_book_text_data.py，把修好的資料重新轉成 {代碼}_data.js，")
        print("然後重新整理瀏覽器（記得用HTTP伺服器方式開啟）確認經文正常顯示。")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
D6經文本體轉換腳本：把 bible_data/bible_text/{代碼}.json（A1下載產出，全本聖經三語逐節）
轉成 index.html 可以直接用 <script src="..."> 載入的全域變數格式。

背景：bible_data/bible_text/{代碼}.json 的原始結構本身已經跟前端需要的格式一致
（{ book, book_zh, chapters:{ "1":{verses:{"1":{en,zh,ja}}} } }），完全不需要重新整理欄位，
唯一要做的事情只是「把json內容包成一個JS變數賦值」，因為瀏覽器用<script src>載入.json檔案
不會自動產生全域變數，必須是`const XXX_DATA = {...};`這種JS語法才能被index.html讀到
（跟psalms_data.js的做法完全一樣，只是psalms那份當初是手動包的，這裡用腳本批次處理10卷）。

輸入：bible_data/bible_text/{代碼}.json（10卷或更多，只要有檔案就會處理）
輸出：{代碼}_data.js（直接輸出到跟index.html同一層的專案根目錄），全域變數{代碼}_DATA

用法（主環境，不需要whisperx_env，只用內建json模組）：
  python build_book_text_data.py
"""
import os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIBLE_TEXT_DIR = os.path.join(BASE_DIR, "bible_data", "bible_text")

# D6目前登記在index.html BOOK_TEXT_SOURCES裡、除詩篇外的10卷。
# 詩篇不在這裡處理，因為psalms_data.js是既有檔案，格式較早定案、繼續沿用不動。
BOOK_CODES = ["PRO", "ISA", "ECC", "GEN", "MAT", "MRK", "LUK", "JHN", "REV", "DAN"]


def main():
    if not os.path.isdir(BIBLE_TEXT_DIR):
        print(f"!! 找不到 {BIBLE_TEXT_DIR}，請確認A1下載有沒有跑過、路徑對不對")
        return

    converted = []
    missing = []

    for code in BOOK_CODES:
        src_path = os.path.join(BIBLE_TEXT_DIR, f"{code}.json")
        if not os.path.exists(src_path):
            missing.append(code)
            continue

        with open(src_path, encoding="utf-8") as f:
            data = json.load(f)

        chapter_count = len(data.get("chapters", {}))
        verse_count = sum(len(ch.get("verses", {})) for ch in data.get("chapters", {}).values())

        out_path = os.path.join(BASE_DIR, f"{code}_data.js")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"// 自動產生檔案，請勿手動編輯 —— 執行 build_book_text_data.py 重新產生\n")
            f.write(f"// 來源：bible_data/bible_text/{code}.json（A1下載產出）\n\n")
            f.write(f"const {code}_DATA = ")
            json.dump(data, f, ensure_ascii=False)
            f.write(";\n")

        converted.append((code, chapter_count, verse_count))
        print(f"{code}：{chapter_count}章、{verse_count}節 → 寫入 {out_path}")

    if missing:
        print(f"\n⚠ 找不到原始檔案、跳過的書卷（{len(missing)}個）：{missing}")
        print("  這些卷在index.html裡會維持顯示「尚未接入經文資料庫」提示，不影響其他卷正常運作。")
        print("  若之後補齊這些json檔案，重跑本腳本一次即可自動補上，不需要改index.html。")

    print(f"\n完成：成功轉換{len(converted)}/{len(BOOK_CODES)}卷。")
    print("接下來請把這些新產生的 {代碼}_data.js 檔案跟 index.html 放在同一個資料夾，")
    print("用瀏覽器（本機HTTP伺服器方式）打開測試每一卷是否正常顯示經文。")


if __name__ == "__main__":
    main()

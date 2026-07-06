# -*- coding: utf-8 -*-
"""
下載 Wiktionary「日本語 慣用句」分類第2頁，補齊第1頁沒抓完的部分
（第1頁199條，全部約311條，第2頁大約還有112條）。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe download_js_page2.py
"""
import os
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data", "idiom_libraries", "JS")
os.makedirs(OUT_DIR, exist_ok=True)

URL = "https://ja.wiktionary.org/w/index.php"
PARAMS = {
    "title": "カテゴリ:日本語_慣用句",
    "pagefrom": "とうのむかし とうのむかし\nとうのむかし",
}

def main():
    resp = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=15)
    resp.encoding = resp.apparent_encoding
    out_path = os.path.join(OUT_DIR, "wiktionary_category_page2.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"已存檔：{out_path}（{len(resp.text)} 字元）")
    print("請把這個檔案上傳給AI，繼續解析剩餘條目。")

if __name__ == "__main__":
    main()

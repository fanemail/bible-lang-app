# -*- coding: utf-8 -*-
"""
探測腳本：抓取三語各一小份樣本的「原始HTML」，存成本地檔案。
純偵查用，不解析、不寫入任何資料庫，只是把原始網頁內容存下來，
讓我們能看到Python實際抓到的HTML長什麼樣（跟網頁瀏覽器看到的不一定一樣）。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe probe_psalms_sources.py
"""
import os
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_samples")
os.makedirs(OUT_DIR, exist_ok=True)

TARGETS = [
    ("english_psalm1.html", "https://ebible.org/engwebp/PSA001.htm"),
    ("chinese_psalm1.html", "https://ebible.org/cmn-cu89t/PSA001.htm"),
    ("japanese_psalms_full.html", "https://jpn.bible/kougo/ps"),
]

def main():
    for filename, url in TARGETS:
        print(f"抓取：{url} ...")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.encoding = resp.apparent_encoding
            out_path = os.path.join(OUT_DIR, filename)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(resp.text)
            print(f"  已存檔：{out_path}（大小：{len(resp.text)} 字元）")
        except Exception as e:
            print(f"  失敗：{e}")

    print(f"\n全部完成，檔案都在：{OUT_DIR}")
    print("請把 english_psalm1.html 和 chinese_psalm1.html 這兩個檔案上傳給我")
    print("（japanese_psalms_full.html 檔案較大，如果上傳有困難，")
    print("可以只複製檔案裡「Psalm 1」對應段落的原始碼貼給我看）")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
下載語塊比對庫（任務A4）確認可行的五個來源的原始資料。
這一步只負責「把原始檔案抓下來」，不做內容解析——PDF裡的表格要抽取成
可用的JSON清單，屬於下一步（等你看過原始檔案內容之後再處理，避免又一次憑猜測寫解析）。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe download_idiom_libraries.py
"""
import os
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data", "idiom_libraries")

TARGETS = [
    ("IS", "rafatbakhsh_2020_most_frequent_idioms.pdf",
     "https://are.ui.ac.ir/article_24238_d247a71eb2906e5271d5d9ac5cff5680.pdf"),
    ("IC", "rafatbakhsh_2019_thematic_idioms.pdf",
     "https://link.springer.com/content/pdf/10.1186/s40862-019-0076-4.pdf"),
    ("VS", "martinez_schmitt_2012_phrase_list.pdf",
     "https://www.lextutor.ca/tests/pvst/martinez_schmitt_2012.pdf"),
    ("VC", "mwe_resources_data_sets_page.html",
     "http://multiword.sourceforge.net/PHITE.php?sitesig=FILES&page=FILES_20_Data_Sets"),
]

# Wiktionary日語慣用句分類頁（可能有分頁，先抓第一頁確認結構）
JS_URL = "https://ja.wiktionary.org/wiki/Category:日本語_慣用句"


def download_file(url, dest_path, allow_insecure_fallback=False):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        print(f"  已下載：{dest_path}（{len(resp.content)/1024:.1f} KB）")
        return True
    except requests.exceptions.SSLError as e:
        if allow_insecure_fallback:
            print(f"  SSL憑證驗證失敗（該站點憑證設定有瑕疵），改用略過驗證的方式重試...")
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                resp = requests.get(url, headers=HEADERS, timeout=30, verify=False)
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
                print(f"  已下載（略過SSL驗證）：{dest_path}（{len(resp.content)/1024:.1f} KB）")
                return True
            except Exception as e2:
                print(f"  仍然失敗：{url} - {e2}")
                return False
        print(f"  失敗（SSL）：{url} - {e}")
        return False
    except Exception as e:
        print(f"  失敗：{url} - {e}")
        return False


def main():
    os.makedirs(BASE, exist_ok=True)

    print("=== 下載 IS / IC / VS 論文PDF、VC資源頁 ===")
    for code, filename, url in TARGETS:
        code_dir = os.path.join(BASE, code)
        os.makedirs(code_dir, exist_ok=True)
        dest = os.path.join(code_dir, filename)
        print(f"[{code}] {filename}")
        # IS來源(are.ui.ac.ir)已知有SSL憑證瑕疵，允許略過驗證重試
        ok = download_file(url, dest, allow_insecure_fallback=(code == "IS"))
        if not ok and code == "VC":
            print("  改用更完整的瀏覽器標頭重試一次...")
            browser_headers = dict(HEADERS)
            browser_headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://multiword.sourceforge.net/",
            })
            try:
                resp = requests.get(url, headers=browser_headers, timeout=30)
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    f.write(resp.content)
                print(f"  已下載：{dest}（{len(resp.content)/1024:.1f} KB）")
            except Exception as e:
                print(f"  仍然失敗：{e}")
                print("  這個網站會擋掉程式發出的請求，建議你直接用瀏覽器打開這個網址手動下載：")
                print(f"  {url}")

    print("\n=== 下載 JS：Wiktionary日語慣用句分類頁 ===")
    js_dir = os.path.join(BASE, "JS")
    os.makedirs(js_dir, exist_ok=True)
    download_file(JS_URL, os.path.join(js_dir, "wiktionary_category_page1.html"))

    print("\n=== 預留：使用者自訂短語庫（US） ===")
    us_dir = os.path.join(BASE, "US")
    os.makedirs(us_dir, exist_ok=True)
    readme_path = os.path.join(us_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("這個資料夾保留給使用者自己整理的常用句式短語資料。\n")
        f.write("等資料整理好後，直接放進這個資料夾，之後會設計對應的整合流程。\n")
    print(f"  已建立：{us_dir}")

    print("\n全部完成。")
    print(f"所有檔案存放於：{BASE}")
    print("下一步：把這些PDF/HTML原始檔案的內容（尤其是表格部分）貼給AI看，")
    print("才能寫出正確的解析腳本，把裡面的清單轉成標注任務能用的格式。")
    print("（PDF表格結構複雜，這步不能跳過用猜的，避免重蹈之前資料格式踩坑的覆轍）")


if __name__ == "__main__":
    main()

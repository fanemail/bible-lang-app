# -*- coding: utf-8 -*-
"""
下載詩篇150章的英文（ebible.org / Winfred Henson朗讀）與日文（WordProject口語訳）音頻。
中文音頻（閻大衛和合本）依項目文檔暫緩，這次不處理。

特性：
  - 可斷點續查：已下載的章節（檔案已存在且大小>0）會自動跳過，可隨時中斷、重新執行接續
  - 串流下載，不會一次把整個mp3吃進記憶體
  - 英文檔名不好猜（"Seventy One"這種拼字），改用實際目錄列表解析，不用手刻數字轉英文單字的邏輯
  - 下載完統一改名成 001.mp3 ~ 150.mp3，跟專案其他資料的命名習慣一致
  - 完成後印出總檔案數與總大小，方便你回來後一眼確認有沒有跑完

用法（可以直接掛機跑，跑多久都沒關係，中斷也沒關係）：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe download_psalms_audio.py

需要安裝套件（只需一次，若前面步驟已裝過requests/bs4則不用重裝）：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe -m pip install requests beautifulsoup4
"""
import os
import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data", "audio")
EN_DIR = os.path.join(BASE_DIR, "en", "PSA")
JA_DIR = os.path.join(BASE_DIR, "ja", "PSA")
os.makedirs(EN_DIR, exist_ok=True)
os.makedirs(JA_DIR, exist_ok=True)

EN_INDEX_URL = "http://ebible.org/eng-web/audio/19_Psalms/"
JA_URL_TMPL = "https://www.wordproaudio.net/bibles/app/audio/12/19/{}.mp3"

RETRY_COUNT = 3
DELAY_BETWEEN = 0.5


def download_file(url, dest_path, retries=RETRY_COUNT):
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return True  # 已下載過，跳過（斷點續查）
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, stream=True, timeout=30)
            resp.raise_for_status()
            tmp_path = dest_path + ".part"
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            os.replace(tmp_path, dest_path)  # 完整下載完才正式改名，避免留下半殘檔案
            return True
        except Exception as e:
            print(f"    [重試 {attempt+1}/{retries}] {url} 失敗：{e}")
            time.sleep(2 * (attempt + 1))
    return False


def download_english():
    print("=== 英文詩篇音頻（ebible.org） ===")
    print("讀取目錄列表...")
    resp = requests.get(EN_INDEX_URL, headers=HEADERS, timeout=30)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    seen_chapters = set()
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.lower().endswith(".mp3"):
            continue
        fname = requests.utils.unquote(href)
        m = re.match(r"(\d{4})\s+Psalms", fname)
        if not m:
            continue
        seq = int(m.group(1))
        chapter = seq - 478  # 0479對應第1章
        if chapter < 1 or chapter > 150:
            continue
        if chapter in seen_chapters:
            continue  # 跳過重複檔案（目錄裡第71篇有一份多餘的"(1)"重複檔）
        seen_chapters.add(chapter)
        links.append((chapter, EN_INDEX_URL + href))

    links.sort(key=lambda x: x[0])
    print(f"解析到 {len(links)} 章（應為150章）")

    ok, fail = 0, 0
    for chapter, url in links:
        dest = os.path.join(EN_DIR, f"{chapter:03d}.mp3")
        success = download_file(url, dest)
        if success:
            ok += 1
        else:
            fail += 1
            print(f"    !! 第{chapter}章下載失敗，之後重跑腳本會自動重試")
        if chapter % 20 == 0:
            print(f"  進度：{chapter}/150")
        time.sleep(DELAY_BETWEEN)

    print(f"英文音頻完成：成功{ok}，失敗{fail}\n")


def download_japanese():
    print("=== 日文詩篇音頻（WordProject口語訳） ===")
    ok, fail = 0, 0
    for chapter in range(1, 151):
        url = JA_URL_TMPL.format(chapter)
        dest = os.path.join(JA_DIR, f"{chapter:03d}.mp3")
        success = download_file(url, dest)
        if success:
            ok += 1
        else:
            fail += 1
            print(f"    !! 第{chapter}章下載失敗，之後重跑腳本會自動重試")
        if chapter % 20 == 0:
            print(f"  進度：{chapter}/150")
        time.sleep(DELAY_BETWEEN)

    print(f"日文音頻完成：成功{ok}，失敗{fail}\n")


def summarize():
    print("=== 總結 ===")
    for label, d in [("英文", EN_DIR), ("日文", JA_DIR)]:
        files = [f for f in os.listdir(d) if f.endswith(".mp3")]
        total_bytes = sum(os.path.getsize(os.path.join(d, f)) for f in files)
        print(f"{label}：{len(files)}/150 個檔案，共 {total_bytes/1024/1024:.1f} MB，存放於 {d}")


def main():
    download_english()
    download_japanese()
    summarize()
    print("\n全部完成。若有章節顯示失敗，直接重新執行本腳本即可（已下載的章節會自動跳過，只補失敗的部分）。")


if __name__ == "__main__":
    main()

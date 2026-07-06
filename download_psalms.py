# -*- coding: utf-8 -*-
"""
下載並解析詩篇三語文字（WEB英文 / 和合本中文 / 口語訳日文），輸出成逐節對齊的JSON。

【重要】先用 TEST_CHAPTERS = 3 跑一次，人工檢查 psalms_test_output.json 品質，
確認沒問題後，把 TEST_CHAPTERS 改成 150，重新執行一次，才是正式全卷輸出。

英文/中文：來源是 ebible.org，每章一個網頁，逐章下載解析，可斷點續查。
日文：來源是 jpn.bible，全卷150章在同一頁，一次下載後在本機解析出所有章節。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe download_psalms.py

需要安裝套件（只需一次）：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe -m pip install beautifulsoup4
"""
import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

# ===== 測試開關：先用小範圍確認品質，OK後改成150 =====
TEST_CHAPTERS = 3   # <-- 確認品質後，把這裡改成 150，重新執行

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
os.makedirs(WORK_DIR, exist_ok=True)

CHECKPOINT_PATH = os.path.join(WORK_DIR, "psalms_download_checkpoint.json")
OUTPUT_PATH = os.path.join(WORK_DIR, f"psalms_{'test' if TEST_CHAPTERS < 150 else 'full'}_output.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

EN_URL_TMPL = "https://ebible.org/engwebp/PSA{:03d}.htm"
ZH_URL_TMPL = "https://ebible.org/cmn-cu89t/PSA{:03d}.htm"
JA_URL = "https://jpn.bible/kougo/ps"

LINE_CLASSES = {"q", "q1", "q2", "q3", "q4", "p", "pi", "pi1", "pi2", "m", "mi", "li", "li1", "li2"}


# ---------- 英文/中文共用解析（ebible.org同一套Haiola系統） ----------
def parse_ebible_chapter(html):
    """回傳 {節號(str): 文字} """
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("div", class_="main")
    if not main:
        return {}
    # 移除註腳（英文版有，中文版通常沒有，沒有就不影響）
    for tag in main.find_all("a", class_="notemark"):
        tag.decompose()

    verses = {}
    current_verse = None
    for div in main.find_all("div", recursive=False):
        classes = div.get("class", [])
        cls0 = classes[0] if classes else ""
        if cls0 not in LINE_CLASSES:
            continue  # 跳過 mt/ms/chapterlabel/s/b/footnote/copyright 等非經文內容

        verse_span = div.find("span", class_="verse")
        if verse_span:
            vid = verse_span.get("id", "")
            vnum = vid.lstrip("V")
            verse_span.decompose()  # 拿掉節號本身的文字，剩下的才是經文內容
            text = div.get_text().strip()
            current_verse = vnum
            verses[current_verse] = text
        else:
            if current_verse is not None:
                text = div.get_text().strip()
                verses[current_verse] = (verses[current_verse] + " " + text).strip()
    return verses


def fetch_ebible_chapter(url_tmpl, chapter_num, retries=3):
    url = url_tmpl.format(chapter_num)
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.encoding = resp.apparent_encoding
            return parse_ebible_chapter(resp.text)
        except Exception as e:
            print(f"    [重試 {attempt+1}] {url} 失敗：{e}")
            time.sleep(1.5 * (attempt + 1))
    return None


# ---------- 日文解析（jpn.bible，全卷一頁） ----------
def parse_japanese_book(html, max_chapter):
    soup = BeautifulSoup(html, "html.parser")

    # 去除注音假名，只留漢字本體
    for rt in soup.find_all("rt"):
        rt.decompose()
    for rp in soup.find_all("rp"):
        rp.decompose()
    # 去除節號數字本身（我們從id屬性取節號，不需要顯示文字裡的數字）
    for vn in soup.find_all("span", class_="verse-number"):
        vn.decompose()

    main = soup.find("main", class_="book")
    book = {}
    if not main:
        return book

    for chapter_div in main.find_all("div", id=True, recursive=False):
        chap_id = chapter_div.get("id", "")
        if not chap_id.isdigit():
            continue
        chapter_num = int(chap_id)
        if chapter_num > max_chapter:
            continue

        verses = {}
        current_verse = None
        buffer = []
        for elem in chapter_div.descendants:
            if isinstance(elem, Tag) and elem.name == "span":
                classes = elem.get("class", [])
                if "verse" in classes:
                    vid = elem.get("id")
                    if vid and ":" in vid:
                        if current_verse is not None and buffer:
                            verses[current_verse] = (verses.get(current_verse, "") + "".join(buffer)).strip()
                            buffer = []
                        current_verse = vid.split(":")[1]
                    continue
            if isinstance(elem, NavigableString):
                if elem.parent and elem.parent.name == "title":
                    continue  # 跳過詩篇標題／背景說明句（如「大衛逃避押沙龍時作的」）
                if current_verse is not None:
                    buffer.append(str(elem))
        if current_verse is not None and buffer:
            verses[current_verse] = (verses.get(current_verse, "") + "".join(buffer)).strip()

        book[chapter_num] = verses

    return book


# ---------- 主流程 ----------
def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"en": {}, "zh": {}}


def save_checkpoint(cp):
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(cp, f, ensure_ascii=False, indent=2)


def main():
    checkpoint = load_checkpoint()

    print(f"=== 下載英文（WEB）1~{TEST_CHAPTERS}章 ===")
    for n in range(1, TEST_CHAPTERS + 1):
        if str(n) in checkpoint["en"]:
            continue
        print(f"  英文 第{n}章 ...")
        verses = fetch_ebible_chapter(EN_URL_TMPL, n)
        if verses:
            checkpoint["en"][str(n)] = verses
            save_checkpoint(checkpoint)
        else:
            print(f"    !! 第{n}章下載失敗，稍後重跑本腳本會自動重試")
        time.sleep(0.3)

    print(f"=== 下載中文（和合本）1~{TEST_CHAPTERS}章 ===")
    for n in range(1, TEST_CHAPTERS + 1):
        if str(n) in checkpoint["zh"]:
            continue
        print(f"  中文 第{n}章 ...")
        verses = fetch_ebible_chapter(ZH_URL_TMPL, n)
        if verses:
            checkpoint["zh"][str(n)] = verses
            save_checkpoint(checkpoint)
        else:
            print(f"    !! 第{n}章下載失敗，稍後重跑本腳本會自動重試")
        time.sleep(0.3)

    print(f"=== 下載日文（口語訳）全卷，取前{TEST_CHAPTERS}章 ===")
    resp = requests.get(JA_URL, headers=HEADERS, timeout=30)
    resp.encoding = resp.apparent_encoding
    ja_book = parse_japanese_book(resp.text, TEST_CHAPTERS)
    print(f"  日文解析完成，取得 {len(ja_book)} 章")

    # ---------- 合併成逐節對齊結構 ----------
    result = {"book": "psalms", "chapters": {}}
    for n in range(1, TEST_CHAPTERS + 1):
        en_verses = checkpoint["en"].get(str(n), {})
        zh_verses = checkpoint["zh"].get(str(n), {})
        ja_verses = {str(k): v for k, v in ja_book.get(n, {}).items()}

        all_vnums = sorted(
            set(en_verses.keys()) | set(zh_verses.keys()) | set(ja_verses.keys()),
            key=lambda x: int(x)
        )
        chapter_verses = {}
        for v in all_vnums:
            chapter_verses[v] = {
                "en": en_verses.get(v, ""),
                "zh": zh_verses.get(v, ""),
                "ja": ja_verses.get(v, ""),
            }
        result["chapters"][str(n)] = {"verses": chapter_verses}

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n完成！輸出檔案：{OUTPUT_PATH}")
    print("請打開這個檔案，人工檢查幾節經文，確認三語文字是否對齊、乾淨、沒有缺漏。")
    print("確認沒問題後，把腳本開頭的 TEST_CHAPTERS 改成 150，重新執行本腳本做全卷下載。")


if __name__ == "__main__":
    main()

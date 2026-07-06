# -*- coding: utf-8 -*-
"""
下載全本聖經66卷的三語逐節文字（英文WEB / 中文和合本 / 日文口語訳）。
解析邏輯完全沿用 download_psalms_full.py（已用詩篇150章驗證過），
這裡只是把「單一書卷」的邏輯泛化成「66卷迴圈」。

輸出：每卷一個獨立json檔案，E:\\bible-lang-app\\bible_data\\bible_text\\{英文代碼}.json
      （不是全部塞一個大檔案，方便之後個別書卷要重跑時不用動到其他卷）

用法（可以掛機跑，會花一些時間，66卷每卷都要逐章下載英文+中文網頁）：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe download_bible_full.py

需要套件：requests, beautifulsoup4（前面步驟應該都裝過了）
"""
import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
OUTPUT_DIR = os.path.join(WORK_DIR, "bible_text")
os.makedirs(OUTPUT_DIR, exist_ok=True)

EN_URL_TMPL = "https://ebible.org/engwebp/{code}{ch}.htm"
ZH_URL_TMPL = "https://ebible.org/cmn-cu89t/{code}{ch}.htm"
JA_URL_TMPL = "https://jpn.bible/kougo/{code}"

LINE_CLASSES = {"q", "q1", "q2", "q3", "q4", "p", "pi", "pi1", "pi2", "m", "mi", "li", "li1", "li2"}

# ===== 66卷書卷代碼對照表：(中文書名, ebible.org代碼[英文/中文共用], jpn.bible代碼, 大約章數) =====
BOOKS = [
    ("創世記","GEN","gen",50), ("出埃及記","EXO","exod",40), ("利未記","LEV","lev",27),
    ("民數記","NUM","num",36), ("申命記","DEU","deut",34), ("約書亞記","JOS","josh",24),
    ("士師記","JDG","judg",21), ("路得記","RUT","ruth",4), ("撒母耳記上","1SA","1sam",31),
    ("撒母耳記下","2SA","2sam",24), ("列王紀上","1KI","1kgs",22), ("列王紀下","2KI","2kgs",25),
    ("歷代志上","1CH","1chr",29), ("歷代志下","2CH","2chr",36), ("以斯拉記","EZR","ezra",10),
    ("尼希米記","NEH","neh",13), ("以斯帖記","EST","esth",10), ("約伯記","JOB","job",42),
    ("詩篇","PSA","ps",150), ("箴言","PRO","prov",31), ("傳道書","ECC","eccl",12),
    ("雅歌","SNG","song",8), ("以賽亞書","ISA","isa",66), ("耶利米書","JER","jer",52),
    ("耶利米哀歌","LAM","lam",5), ("以西結書","EZK","ezek",48), ("但以理書","DAN","dan",12),
    ("何西阿書","HOS","hos",14), ("約珥書","JOL","joel",3), ("阿摩司書","AMO","amos",9),
    ("俄巴底亞書","OBA","obad",1), ("約拿書","JON","jonah",4), ("彌迦書","MIC","mic",7),
    ("那鴻書","NAM","nah",3), ("哈巴谷書","HAB","hab",3), ("西番雅書","ZEP","zeph",3),
    ("哈該書","HAG","hag",2), ("撒迦利亞書","ZEC","zech",14), ("瑪拉基書","MAL","mal",4),
    ("馬太福音","MAT","matt",28), ("馬可福音","MRK","mark",16), ("路加福音","LUK","luke",24),
    ("約翰福音","JHN","john",21), ("使徒行傳","ACT","acts",28), ("羅馬書","ROM","rom",16),
    ("哥林多前書","1CO","1cor",16), ("哥林多後書","2CO","2cor",13), ("加拉太書","GAL","gal",6),
    ("以弗所書","EPH","eph",6), ("腓立比書","PHP","phil",4), ("歌羅西書","COL","col",4),
    ("帖撒羅尼迦前書","1TH","1thess",5), ("帖撒羅尼迦後書","2TH","2thess",3),
    ("提摩太前書","1TI","1tim",6), ("提摩太後書","2TI","2tim",4), ("提多書","TIT","titus",3),
    ("腓利門書","PHM","phlm",1), ("希伯來書","HEB","heb",13), ("雅各書","JAS","jas",5),
    ("彼得前書","1PE","1pet",5), ("彼得後書","2PE","2pet",3), ("約翰一書","1JN","1john",5),
    ("約翰二書","2JN","2john",1), ("約翰三書","3JN","3john",1), ("猶大書","JUD","jude",1),
    ("啟示錄","REV","rev",22),
]


# 中文來源網頁的段落結構：只有每段第一節有HTML節號標記，段落內後續節號
# 是直接寫在文字裡的純文字（例如「...非常混沌。 2　地是空虛混沌...」），
# 這個「2」後面緊接的是不斷行空格(U+00A0)，英文文字本身不會有這種「阿拉伯數字+
# 不斷行空格」的搭配，中文數字寫法（九百三十歲）也不會，所以這個pattern能準確
# 只命中真正的內嵌節號標記，不會誤判。
INLINE_VERSE_MARKER_RE = re.compile(r'(\d{1,3})\xa0')


def split_inline_verse_markers(current_verse, text, verses):
    """把div文字裡「內嵌純文字節號」標記出的後續節，從目前這節的文字裡拆出來，
       分別寫回verses字典對應的節號。回傳「屬於current_verse自己」的那一段文字。
       只有中文來源會用到（英文/日文各自的解析函式沒有呼叫這個函式）。"""
    matches = list(INLINE_VERSE_MARKER_RE.finditer(text))
    if not matches:
        return text
    owner = current_verse
    cursor = 0
    own_text = None
    for m in matches:
        segment = text[cursor:m.start()].strip()
        if owner == current_verse:
            own_text = segment
        else:
            verses[owner] = ((verses.get(owner, "") + " " + segment).strip() if segment else verses.get(owner, ""))
        owner = m.group(1)
        cursor = m.end()
    # 最後一段（最後一個標記之後的文字）
    tail = text[cursor:].strip()
    if owner == current_verse:
        own_text = (own_text + " " + tail).strip() if own_text else tail
    else:
        verses[owner] = ((verses.get(owner, "") + " " + tail).strip() if tail else verses.get(owner, ""))
    return own_text if own_text is not None else ""


def parse_ebible_chapter(html, is_chinese=False):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("div", class_="main")
    if not main:
        return {}
    for tag in main.find_all("a", class_="notemark"):
        tag.decompose()
    verses = {}
    current_verse = None
    for div in main.find_all("div", recursive=False):
        classes = div.get("class", [])
        cls0 = classes[0] if classes else ""
        if cls0 not in LINE_CLASSES:
            continue
        verse_span = div.find("span", class_="verse")
        if verse_span:
            vid = verse_span.get("id", "")
            m = re.match(r'V?(\d+)', vid)
            if not m:
                verse_span.decompose()
                continue
            vnum = m.group(1)
            verse_span.decompose()
            text = div.get_text().strip()
            current_verse = vnum
            if is_chinese:
                verses[current_verse] = split_inline_verse_markers(current_verse, text, verses)
            else:
                verses[current_verse] = text
        else:
            if current_verse is not None:
                text = div.get_text().strip()
                if is_chinese:
                    own_text = split_inline_verse_markers(current_verse, text, verses)
                    verses[current_verse] = (verses[current_verse] + " " + own_text).strip() if own_text else verses[current_verse]
                else:
                    verses[current_verse] = (verses[current_verse] + " " + text).strip()
    return verses


def fetch_ebible_chapter(url, retries=3, is_chinese=False):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 404:
                return None  # 章節不存在（超出範圍），正常結束訊號
            resp.encoding = resp.apparent_encoding
            return parse_ebible_chapter(resp.text, is_chinese=is_chinese)
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return "ERROR"  # 連線問題，非章節不存在


def parse_japanese_book(html):
    soup = BeautifulSoup(html, "html.parser")
    for rt in soup.find_all("rt"):
        rt.decompose()
    for rp in soup.find_all("rp"):
        rp.decompose()
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
        verses = {}
        current_verse = None
        buffer = []
        for elem in chapter_div.descendants:
            if isinstance(elem, Tag) and elem.name == "span":
                classes = elem.get("class", [])
                if "verse" in classes:
                    vid = elem.get("id")
                    if vid and ":" in vid:
                        vpart = vid.split(":", 1)[1]
                        m = re.match(r'(\d+)', vpart)
                        if not m:
                            continue
                        if current_verse is not None and buffer:
                            verses[current_verse] = (verses.get(current_verse, "") + "".join(buffer)).strip()
                            buffer = []
                        current_verse = m.group(1)
                    continue
            if isinstance(elem, NavigableString):
                if elem.parent and elem.parent.name == "title":
                    continue
                if current_verse is not None:
                    buffer.append(str(elem))
        if current_verse is not None and buffer:
            verses[current_verse] = (verses.get(current_verse, "") + "".join(buffer)).strip()
        book[chapter_num] = verses
    return book


def is_corrupted(filepath):
    """偵測既有檔案是否為「英中文全空」的壞資料（上一版padding bug留下的），若是則要重跑"""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        total = 0
        empty_en = 0
        for ch_obj in data["chapters"].values():
            for v in ch_obj["verses"].values():
                total += 1
                if not v.get("en"):
                    empty_en += 1
        return total > 0 and empty_en == total  # 100%缺英文 = 壞資料
    except Exception:
        return True  # 讀不出來也視為壞資料，重跑


def download_book(zh_name, en_code, ja_code, max_chapters):
    output_path = os.path.join(OUTPUT_DIR, f"{en_code}.json")
    if os.path.exists(output_path):
        if not is_corrupted(output_path):
            print(f"  [{en_code}] {zh_name}：已存在且正常，跳過")
            return
        else:
            print(f"  [{en_code}] {zh_name}：偵測到舊檔案是壞資料（英文全空，上版padding bug），重新下載")

    print(f"  [{en_code}] {zh_name}：開始下載...")

    # 補零位數：預設2位數，只有章數超過99的書卷（目前只有詩篇）才用3位數
    pad_width = max(2, len(str(max_chapters)))

    en_chapters = {}
    ch = 1
    while ch <= max_chapters + 5:
        ch_str = str(ch).zfill(pad_width)
        result = fetch_ebible_chapter(EN_URL_TMPL.format(code=en_code, ch=ch_str))
        if result is None:
            break
        if result == "ERROR":
            print(f"    !! 英文第{ch}章連線失敗，跳過這章")
            ch += 1
            continue
        en_chapters[str(ch)] = result
        ch += 1
        time.sleep(0.2)

    zh_chapters = {}
    ch = 1
    while ch <= max_chapters + 5:
        ch_str = str(ch).zfill(pad_width)
        result = fetch_ebible_chapter(ZH_URL_TMPL.format(code=en_code, ch=ch_str), is_chinese=True)
        if result is None:
            break
        if result == "ERROR":
            print(f"    !! 中文第{ch}章連線失敗，跳過這章")
            ch += 1
            continue
        zh_chapters[str(ch)] = result
        ch += 1
        time.sleep(0.2)

    ja_book = {}
    try:
        resp = requests.get(JA_URL_TMPL.format(code=ja_code), headers=HEADERS, timeout=30)
        resp.encoding = resp.apparent_encoding
        ja_book = parse_japanese_book(resp.text)
    except Exception as e:
        print(f"    !! 日文下載失敗：{e}")

    total_chapters = max(len(en_chapters), len(zh_chapters), len(ja_book))
    result = {"book": en_code, "book_zh": zh_name, "chapters": {}}
    for n in range(1, total_chapters + 1):
        en_v = en_chapters.get(str(n), {})
        zh_v = zh_chapters.get(str(n), {})
        ja_v = {str(k): v for k, v in ja_book.get(n, {}).items()}
        vnums = sorted(
            (v for v in (set(en_v) | set(zh_v) | set(ja_v)) if v.isdigit()),
            key=int
        )
        chapter_verses = {}
        for v in vnums:
            chapter_verses[v] = {"en": en_v.get(v, ""), "zh": zh_v.get(v, ""), "ja": ja_v.get(v, "")}
        if chapter_verses:
            result["chapters"][str(n)] = {"verses": chapter_verses}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    print(f"    完成：{len(result['chapters'])}章，已寫出 {output_path}")


def main():
    print(f"共 {len(BOOKS)} 卷待處理\n")
    for i, (zh_name, en_code, ja_code, max_ch) in enumerate(BOOKS, 1):
        print(f"[{i}/{len(BOOKS)}]", end=" ")
        download_book(zh_name, en_code, ja_code, max_ch)

    print("\n全部完成。個別書卷若下載失敗或不完整，把對應的 bible_text/{代碼}.json 刪除，重新執行本腳本即可單獨補該卷。")


if __name__ == "__main__":
    main()

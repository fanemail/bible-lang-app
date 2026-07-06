# -*- coding: utf-8 -*-
"""
下載10卷書英文（ebible.org LibriVox eng-web版）與日文（WordProject口語訳）音頻。
可斷點續查：已下載檔案自動跳過。重新執行只補失敗的章節。
用法（3.14主環境）：python download_audio_multi.py
"""
import os, re, time, requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data", "audio")

# (書卷代碼, ebible目錄名稱, WordProject書卷號, 總章數)
BOOKS = [
    ("PRO", "20_Proverbs",     20, 31),
    ("ISA", "23_Isaiah",       23, 66),
    ("ECC", "21_Ecclesiastes", 21, 12),
    ("GEN", "01_Genesis",       1, 50),
    ("MAT", "40_Matthew",      40, 28),
    ("MRK", "41_Mark",         41, 16),
    ("LUK", "42_Luke",         42, 24),
    ("JHN", "43_John",         43, 21),
    ("REV", "66_Revelations",  66, 22),
    ("DAN", "27_Daniel",       27, 12),
]

EN_BASE = "https://ebible.org/eng-web/audio/"
JA_TMPL = "https://www.wordproaudio.net/bibles/app/audio/12/{}/{}.mp3"

def download_file(url, dest, retries=3):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
            r.raise_for_status()
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(65536):
                    if chunk: f.write(chunk)
            os.replace(tmp, dest)
            return True
        except Exception as e:
            print(f"    [重試{attempt+1}] {e}")
            time.sleep(2*(attempt+1))
    return False

def download_en_book(code, dir_name, max_ch):
    out_dir = os.path.join(BASE_DIR, "en", code)
    os.makedirs(out_dir, exist_ok=True)
    idx_url = EN_BASE + dir_name + "/"
    print(f"  讀取英文目錄：{idx_url}")
    try:
        r = requests.get(idx_url, headers=HEADERS, timeout=30)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  !! 目錄讀取失敗：{e}")
        return 0, 1
    book_en = dir_name.split("_", 1)[1]
    all_hrefs = [a["href"] for a in soup.find_all("a", href=True)]
    mp3_hrefs = [h for h in all_hrefs if h.lower().endswith(".mp3")]
    # 英文拼字數字轉換表（用於"Chapter One"/"Chapter Sixty-Six"這種檔名，最大支援到99，
    # 已足夠覆蓋這批書卷的最大章數66）
    _ONES = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9}
    _TEENS = {"ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,
              "sixteen":16,"seventeen":17,"eighteen":18,"nineteen":19}
    _TENS = {"twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,"seventy":70,"eighty":80,"ninety":90}
    def words_to_num(s):
        total = 0
        for part in re.split(r'[\s\-]+', s.strip().lower()):
            if part in _ONES: total += _ONES[part]
            elif part in _TEENS: total += _TEENS[part]
            elif part in _TENS: total += _TENS[part]
            else: return None
        return total if total > 0 else None

    links = {}
    unmatched = []
    for href in mp3_hrefs:
        fname = requests.utils.unquote(href)
        basename = fname.rsplit("/", 1)[-1]
        ch = None
        # 命名規則一（箴言等）：章節數字在檔名結尾，例如 ...-01.mp3
        m = re.search(r'(\d+)\.mp3$', basename, re.IGNORECASE)
        if m:
            ch = int(m.group(1))
        else:
            # 命名規則二（以賽亞書/馬太福音/約翰福音等）：檔名裡開頭的數字是全站全域編號（跟章節無關），
            # 真正的章節資訊藏在拼出來的英文字裡，例如"...Chapter One.mp3"、"...Chapter Sixty-Six.mp3"。
            # 命名規則二（以賽亞書/創世記/馬太福音等）：檔名裡開頭的數字是全站全域編號（跟章節無關），
            # 真正的章節資訊藏在拼出來的英文字裡，例如"...Chapter One.mp3"、
            # "...Chapter Twenty One.mp3"（空格分隔）、"...Chapter_Twenty_One.mp3"（底線分隔，創世記這種），
            # 偶爾還會帶括號備註如"...Chapter Seventeen (1).mp3"（同一章的另一個錄音版本，忽略備註即可）。
            m2 = re.search(r'chapter[\s_]+([a-zA-Z\s_\-()0-9]+?)\.mp3$', basename, re.IGNORECASE)
            if m2:
                raw = re.sub(r'\([^)]*\)', '', m2.group(1))  # 去掉括號備註
                tokens = [t for t in re.split(r'[\s_\-]+', raw.strip().lower()) if t]
                ch = words_to_num(' '.join(tokens))
        if ch is None:
            unmatched.append(basename)
            continue
        if 1 <= ch <= max_ch and ch not in links:
            links[ch] = idx_url + href
    if not links:
        print(f"  !! 目錄解析到0個檔案，請人工確認URL：{idx_url}")
        print(f"  -- 診斷資訊：頁面總連結數={len(all_hrefs)}，其中.mp3結尾連結數={len(mp3_hrefs)}")
        if mp3_hrefs:
            print(f"  -- 前5個.mp3連結範例（用來判斷章節數字抓取規則是否吻合）：")
            for h in mp3_hrefs[:5]:
                print(f"       {h}")
        elif all_hrefs:
            print(f"  -- 找不到任何.mp3連結，前5個連結範例（判斷頁面結構是否不同）：")
            for h in all_hrefs[:5]:
                print(f"       {h}")
        return 0, 1
    if unmatched:
        print(f"  -- 提醒：有{len(unmatched)}個.mp3連結兩種命名規則都對不上，範例：{unmatched[:3]}")
    if len(links) < max_ch:
        print(f"  -- 提醒：只抓到{len(links)}/{max_ch}章，可能有部分章節檔名規則跟正規表達式不吻合，建議完成後核對章數是否足夠")
    ok = fail = 0
    for ch in sorted(links):
        dest = os.path.join(out_dir, f"{ch:03d}.mp3")
        if download_file(links[ch], dest):
            ok += 1
        else:
            fail += 1
            print(f"  !! {code}英文第{ch}章失敗")
        time.sleep(0.5)
    print(f"  英文{code}完成：{ok}章OK，{fail}章失敗（目錄共{len(links)}章，預期{max_ch}）")
    return ok, fail

def download_ja_book(code, ja_num, max_ch):
    out_dir = os.path.join(BASE_DIR, "ja", code)
    os.makedirs(out_dir, exist_ok=True)
    ok = fail = 0
    for ch in range(1, max_ch + 1):
        url = JA_TMPL.format(ja_num, ch)
        dest = os.path.join(out_dir, f"{ch:03d}.mp3")
        if download_file(url, dest):
            ok += 1
        else:
            fail += 1
            print(f"  !! {code}日文第{ch}章失敗")
        time.sleep(0.5)
    print(f"  日文{code}完成：{ok}章OK，{fail}章失敗")
    return ok, fail

def summarize():
    print(f"\n{'='*50}\n總結：")
    grand_total = 0
    for code, _, _, _ in BOOKS:
        for lang in ("en", "ja"):
            d = os.path.join(BASE_DIR, lang, code)
            if not os.path.exists(d):
                continue
            files = [f for f in os.listdir(d) if f.endswith(".mp3")]
            mb = sum(os.path.getsize(os.path.join(d, f)) for f in files) / 1024 / 1024
            grand_total += mb
            print(f"  {lang}/{code}：{len(files)}個檔案，{mb:.1f}MB")
    print(f"合計：{grand_total:.0f}MB")

def main():
    print(f"共{len(BOOKS)}卷待下載（英文+日文），可隨時中斷重執行\n")
    total_ok = total_fail = 0
    for code, dir_name, ja_num, max_ch in BOOKS:
        print(f"\n{'='*50}")
        print(f"[{code}] 共{max_ch}章")
        ok_en, fail_en = download_en_book(code, dir_name, max_ch)
        ok_ja, fail_ja = download_ja_book(code, ja_num, max_ch)
        total_ok += ok_en + ok_ja
        total_fail += fail_en + fail_ja
    summarize()
    print(f"\n全部完成。總成功{total_ok}個，失敗{total_fail}個。")
    if total_fail:
        print("有失敗的章節，重新執行本腳本即可自動補齊（已下載的會跳過）。")

if __name__ == "__main__":
    main()

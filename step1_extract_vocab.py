# -*- coding: utf-8 -*-
"""
階段一：從WEB聖經全文提取英文詞彙清單
========================================
用途：下載ebible.org官方WEB聖經整本HTML包，解壓後過濾出66卷正典（排除次經），
      斷詞、正規化，產出約14,000詞的清單，存成 vocab_list.json。

這一步是純本地文字處理，跑起來只需要幾秒到幾分鐘（取決於下載速度），
不需要斷點續查機制，執行完就結束。

執行方式（Windows CMD）：
"C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" step1_extract_vocab.py

需要先安裝套件（只需跑一次）：
"C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" -m pip install requests

如果環境有裝 nltk，會自動使用WordNet做詞形還原（去時態/複數），
沒裝的話會退回簡易正規化（效果較粗略，但不影響整體流程可以先跑起來）。
"""

import os
import re
import json
import zipfile
import html
import urllib.request

# ---------- 設定 ----------
ZIP_URL = "https://ebible.org/Scriptures/eng-web_html.zip"
WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
ZIP_PATH = os.path.join(WORK_DIR, "eng-web_html.zip")
EXTRACT_DIR = os.path.join(WORK_DIR, "eng-web_html")
OUTPUT_PATH = os.path.join(WORK_DIR, "vocab_list.json")
PROPER_NOUNS_PATH = os.path.join(WORK_DIR, "proper_nouns.json")

# 66卷正典書卷代碼（依照ebible.org的檔名前綴），排除次經/次典
CANONICAL_BOOKS = [
    "GEN","EXO","LEV","NUM","DEU","JOS","JDG","RUT","1SA","2SA",
    "1KI","2KI","1CH","2CH","EZR","NEH","EST","JOB","PSA","PRO",
    "ECC","SNG","ISA","JER","LAM","EZK","DAN","HOS","JOL","AMO",
    "OBA","JON","MIC","NAM","HAB","ZEP","HAG","ZEC","MAL",
    "MAT","MRK","LUK","JHN","ACT","ROM","1CO","2CO","GAL","EPH",
    "PHP","COL","1TH","2TH","1TI","2TI","TIT","PHM","HEB","JAS",
    "1PE","2PE","1JN","2JN","3JN","JUD","REV"
]

# ---------- 詞形還原（優先用nltk，沒有就退回簡易規則） ----------
try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import wordnet

    def _ensure_nltk_data(pkg_id, download_name):
        try:
            nltk.data.find(pkg_id)
        except LookupError:
            print(f"首次使用，正在下載nltk資源：{download_name} ...")
            nltk.download(download_name)

    _ensure_nltk_data('corpora/wordnet', 'wordnet')
    _ensure_nltk_data('corpora/omw-1.4', 'omw-1.4')
    # 不同nltk版本的詞性標註器資源名稱不同，兩個都嘗試
    try:
        _ensure_nltk_data('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng')
    except Exception:
        pass
    try:
        _ensure_nltk_data('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger')
    except Exception:
        pass

    _lemmatizer = WordNetLemmatizer()

    def _wordnet_pos(treebank_tag):
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        return wordnet.NOUN

    def lemmatize_tokens(tokens):
        """對一整串按原文順序排列的詞做詞性標註，回傳 (原詞, 詞性, 還原後詞根) 的清單。"""
        tagged = nltk.pos_tag(tokens)
        result = []
        for w, tag in tagged:
            lemma = _lemmatizer.lemmatize(w.lower(), pos=_wordnet_pos(tag))
            result.append((w, tag, lemma))
        return result

    print("已使用nltk（含詞性標註）做詞形還原（品質較佳）。")
    USE_NLTK = True
except ImportError:
    print("未安裝nltk，改用簡易規則做詞形還原（品質較粗略，之後可補裝nltk重跑這一步）。")
    USE_NLTK = False

    def lemmatize_tokens(tokens):
        """無nltk時的備援：無法判斷詞性，也無法區分專有名詞，全部當一般詞處理。"""
        result = []
        for word in tokens:
            w = word.lower()
            if w.endswith("'s"):
                w = w[:-2]
            if w.endswith("ies") and len(w) > 4:
                lemma = w[:-3] + "y"
            elif (w.endswith("es") or w.endswith("s")) and len(w) > 3 and not w.endswith("ss"):
                lemma = w[:-2] if w.endswith("es") else w[:-1]
            else:
                lemma = w
            result.append((word, "UNKNOWN", lemma))
        return result


def download_zip():
    os.makedirs(WORK_DIR, exist_ok=True)
    if os.path.exists(ZIP_PATH):
        print(f"已存在下載檔，跳過下載：{ZIP_PATH}")
        return
    print(f"下載中：{ZIP_URL}")
    req = urllib.request.Request(
        ZIP_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp, open(ZIP_PATH, 'wb') as out_f:
        total = resp.getheader('Content-Length')
        total = int(total) if total else None
        downloaded = 0
        chunk_size = 65536
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r下載進度：{downloaded//1024} KB / {total//1024} KB ({pct:.1f}%)", end="")
        print()
    print("下載完成。")


def extract_zip():
    if os.path.isdir(EXTRACT_DIR) and os.listdir(EXTRACT_DIR):
        print(f"已存在解壓資料夾，跳過解壓：{EXTRACT_DIR}")
        return
    print("解壓中...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(EXTRACT_DIR)
    print("解壓完成。")


def find_book_files():
    """在解壓目錄（含子資料夾）中找出屬於66正典的htm檔案"""
    all_files = []
    for root, _dirs, files in os.walk(EXTRACT_DIR):
        for f in files:
            if f.lower().endswith((".htm", ".html")):
                all_files.append(os.path.join(root, f))
    matched = []
    for path in all_files:
        fname = os.path.basename(path)
        for code in CANONICAL_BOOKS:
            if fname.upper().startswith(code):
                matched.append(path)
                break
    return matched


def extract_words_from_html(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    raw = html.unescape(raw)
    text = re.sub(r'<[^>]+>', ' ', raw)
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)
    return words


def main():
    download_zip()
    extract_zip()
    files = find_book_files()
    print(f"找到 {len(files)} 個章節檔案（66正典）。")
    if not files:
        print("⚠️ 沒有找到任何章節檔案，請檢查解壓目錄結構是否符合預期："
              f"{EXTRACT_DIR}")
        return

    vocab = set()
    proper_nouns = set()
    unknown_pos_count = 0
    for i, path in enumerate(files, 1):
        tokens = extract_words_from_html(path)
        tagged_lemmas = lemmatize_tokens(tokens)
        for word, tag, lemma in tagged_lemmas:
            if tag == "UNKNOWN":
                unknown_pos_count += 1
                if len(lemma) >= 2:
                    vocab.add(lemma)
                continue
            if tag.startswith("NNP"):
                # 專有名詞（人名/地名等）：不進入學習詞彙表，另存一份
                proper_nouns.add(word.lower())
            else:
                if len(lemma) >= 2:
                    vocab.add(lemma)
        if i % 200 == 0:
            print(f"處理進度：{i}/{len(files)} 章節")

    # 專有名詞清單裡，如果同一個詞根同時也在一般詞彙表出現過
    # （某些詞在不同上下文可能被判斷為人名、也可能是普通詞），
    # 以一般詞彙表優先，避免漏掉真正該學的詞。
    proper_nouns = proper_nouns - vocab

    vocab_list = sorted(vocab)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(vocab_list, f, ensure_ascii=False, indent=2)

    proper_noun_list = sorted(proper_nouns)
    with open(PROPER_NOUNS_PATH, 'w', encoding='utf-8') as f:
        json.dump(proper_noun_list, f, ensure_ascii=False, indent=2)

    print(f"完成！一般學習詞彙：{len(vocab_list)} 個，已存到：{OUTPUT_PATH}")
    print(f"      專有名詞（人名/地名，不進學習清單）：{len(proper_noun_list)} 個，已存到：{PROPER_NOUNS_PATH}")
    if not USE_NLTK:
        print("⚠️ 這次沒有用nltk詞性標註，無法區分專有名詞，proper_nouns.json會是空的、"
              "vocab_list.json會混有人名地名，建議確認nltk有正常載入後重跑一次。")
    print("接下來執行 step2_build_vocab_db.py 開始查有道API（這一步會跑比較久，可斷點續查）。")


if __name__ == "__main__":
    main()

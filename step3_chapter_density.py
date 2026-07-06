# -*- coding: utf-8 -*-
"""
階段三：章節學習密度分析（篩選家譜/名單/律法細節等低密度章節）
================================================================
用途：對聖經66卷、每一章分別計算「學習密度分數」，找出：
  - 專有名詞佔比過高的章節（家譜、支派分地、人口普查）
  - 詞彙重複度過高、變化度過低的章節（律法細節、重複套語）
這些章節閱讀負擔大、語塊密度低，適合列為學習優先順序較低的章節。

直接讀取 step1_extract_vocab.py 已經下載解壓好的聖經文字，
不需要重新下載任何東西，跑起來很快（幾分鐘內完成）。

執行方式（Windows CMD，跟之前一樣的資料夾）：
"C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" step3_chapter_density.py

輸出：bible_data\\chapter_density_report.csv（Excel可以直接打開），
     可以用「density_score」欄位排序，分數低的排前面就是建議跳過/延後的章節。
"""

import os
import re
import csv
import html

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_data")
EXTRACT_DIR = os.path.join(WORK_DIR, "eng-web_html")
REPORT_PATH = os.path.join(WORK_DIR, "chapter_density_report.csv")

CANONICAL_BOOKS = [
    "GEN","EXO","LEV","NUM","DEU","JOS","JDG","RUT","1SA","2SA",
    "1KI","2KI","1CH","2CH","EZR","NEH","EST","JOB","PSA","PRO",
    "ECC","SNG","ISA","JER","LAM","EZK","DAN","HOS","JOL","AMO",
    "OBA","JON","MIC","NAM","HAB","ZEP","HAG","ZEC","MAL",
    "MAT","MRK","LUK","JHN","ACT","ROM","1CO","2CO","GAL","EPH",
    "PHP","COL","1TH","2TH","1TI","2TI","TIT","PHM","HEB","JAS",
    "1PE","2PE","1JN","2JN","3JN","JUD","REV"
]

BOOK_NAMES_ZH = {
    "GEN":"創世記","EXO":"出埃及記","LEV":"利未記","NUM":"民數記","DEU":"申命記",
    "JOS":"約書亞記","JDG":"士師記","RUT":"路得記","1SA":"撒母耳記上","2SA":"撒母耳記下",
    "1KI":"列王紀上","2KI":"列王紀下","1CH":"歷代志上","2CH":"歷代志下","EZR":"以斯拉記",
    "NEH":"尼希米記","EST":"以斯帖記","JOB":"約伯記","PSA":"詩篇","PRO":"箴言",
    "ECC":"傳道書","SNG":"雅歌","ISA":"以賽亞書","JER":"耶利米書","LAM":"耶利米哀歌",
    "EZK":"以西結書","DAN":"但以理書","HOS":"何西阿書","JOL":"約珥書","AMO":"阿摩司書",
    "OBA":"俄巴底亞書","JON":"約拿書","MIC":"彌迦書","NAM":"那鴻書","HAB":"哈巴谷書",
    "ZEP":"西番雅書","HAG":"哈該書","ZEC":"撒迦利亞書","MAL":"瑪拉基書",
    "MAT":"馬太福音","MRK":"馬可福音","LUK":"路加福音","JHN":"約翰福音","ACT":"使徒行傳",
    "ROM":"羅馬書","1CO":"哥林多前書","2CO":"哥林多後書","GAL":"加拉太書","EPH":"以弗所書",
    "PHP":"腓立比書","COL":"歌羅西書","1TH":"帖撒羅尼迦前書","2TH":"帖撒羅尼迦後書",
    "1TI":"提摩太前書","2TI":"提摩太後書","TIT":"提多書","PHM":"腓利門書","HEB":"希伯來書",
    "JAS":"雅各書","1PE":"彼得前書","2PE":"彼得後書","1JN":"約翰一書","2JN":"約翰二書",
    "3JN":"約翰三書","JUD":"猶大書","REV":"啟示錄"
}

try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import wordnet
    _lemmatizer = WordNetLemmatizer()

    def _wordnet_pos(tag):
        if tag.startswith('J'):
            return wordnet.ADJ
        elif tag.startswith('V'):
            return wordnet.VERB
        elif tag.startswith('N'):
            return wordnet.NOUN
        elif tag.startswith('R'):
            return wordnet.ADV
        return wordnet.NOUN

    def analyze_tokens(tokens):
        """回傳 (總詞數, 專有名詞數, 相異詞根數)"""
        tagged = nltk.pos_tag(tokens)
        lemmas = set()
        proper_count = 0
        for w, tag in tagged:
            if tag.startswith("NNP"):
                proper_count += 1
            else:
                lemma = _lemmatizer.lemmatize(w.lower(), pos=_wordnet_pos(tag))
                lemmas.add(lemma)
        return len(tokens), proper_count, len(lemmas)

    USE_NLTK = True
    print("已使用nltk（含詞性標註）計算章節密度。")
except ImportError:
    USE_NLTK = False
    print("⚠️ 未安裝nltk，無法準確判斷專有名詞比例，分析結果會不準確，建議先裝好nltk再跑這支。")

    def analyze_tokens(tokens):
        lemmas = set(t.lower() for t in tokens)
        return len(tokens), 0, len(lemmas)


def extract_words_from_html(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        raw = f.read()
    raw = html.unescape(raw)
    text = re.sub(r'<[^>]+>', ' ', raw)
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)


def find_book_chapter_files():
    """回傳 {(book_code, chapter_num): filepath}，依檔名解析章號"""
    result = {}
    for root, _dirs, files in os.walk(EXTRACT_DIR):
        for fname in files:
            if not fname.lower().endswith((".htm", ".html")):
                continue
            upper = fname.upper()
            for code in CANONICAL_BOOKS:
                if upper.startswith(code):
                    rest = upper[len(code):]
                    m = re.match(r"(\d+)", rest)
                    if m:
                        chapter_num = int(m.group(1))
                        result[(code, chapter_num)] = os.path.join(root, fname)
                    break
    return result


def main():
    if not os.path.isdir(EXTRACT_DIR):
        print(f"⚠️ 找不到解壓目錄：{EXTRACT_DIR}，請先執行過 step1_extract_vocab.py。")
        return

    files = find_book_chapter_files()
    print(f"找到 {len(files)} 個章節檔案，開始分析...")

    rows = []
    for i, ((code, chapter), path) in enumerate(sorted(files.items()), 1):
        tokens = extract_words_from_html(path)
        if not tokens:
            continue
        total, proper_count, distinct_count = analyze_tokens(tokens)
        proper_ratio = proper_count / total if total else 0
        distinct_ratio = distinct_count / total if total else 0
        # 密度分數：詞彙多樣性高、專有名詞比例低 → 分數高（值得優先學）
        density_score = round(distinct_ratio * (1 - proper_ratio), 4)

        if proper_ratio > 0.25:
            verdict = "低優先（人名地名密集，疑似家譜/名單/分地）"
        elif density_score < 0.30:
            verdict = "低優先（用詞重複度高，疑似律法細節/重複套語）"
        elif density_score >= 0.45:
            verdict = "優先（語塊密度高）"
        else:
            verdict = "一般"

        rows.append({
            "book_code": code,
            "book_zh": BOOK_NAMES_ZH.get(code, code),
            "chapter": chapter,
            "total_words": total,
            "proper_noun_ratio": round(proper_ratio, 3),
            "distinct_word_ratio": round(distinct_ratio, 3),
            "density_score": density_score,
            "verdict": verdict,
        })

        if i % 200 == 0:
            print(f"分析進度：{i}/{len(files)}")

    rows.sort(key=lambda r: r["density_score"])

    with open(REPORT_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n完成！報告已存到：{REPORT_PATH}（可以直接用Excel打開）")
    print(f"\n===== 密度最低的20章（最建議跳過/延後） =====")
    for r in rows[:20]:
        print(f"{r['book_zh']} {r['chapter']}章｜密度分數{r['density_score']}｜"
              f"專有名詞比例{r['proper_noun_ratio']}｜{r['verdict']}")

    print(f"\n===== 密度最高的20章（最建議優先學） =====")
    for r in rows[-20:][::-1]:
        print(f"{r['book_zh']} {r['chapter']}章｜密度分數{r['density_score']}｜"
              f"專有名詞比例{r['proper_noun_ratio']}｜{r['verdict']}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
merge_chunks.py (多書卷版 v2.0)

用途：
1. 掃描 bible_data 資料夾裡所有書卷的 chunks_en_{書卷}_*.json 和
   chunks_ja_{書卷}_*.json，依書卷分組合併成一份給前端用的 chunks_data.js
2. 對每一卷書分別計算「章節語塊密度」（語塊數/節數），分優先／一般／低優先
   三級，供App目錄UI做顏色深淺分級用
3. 輸出合併後的 chapter_density_report.csv（含書卷欄位）

用法：
    python merge_chunks.py

輸出：
    E:\\bible-lang-app\\chunks_data.js
    E:\\bible-lang-app\\bible_data\\chapter_density_report.csv

【重要：資料結構跟之前只做詩篇時不一樣了】
現在支援多書卷，所以 chunks_data.js 改成用書卷代號分層：
    const CHUNKS_DATA = {
      "PSA": { "en": [...], "ja": [...] },
      "PRO": { "en": [...], "ja": [...] },
      "MAT": { "en": [...], "ja": [...] }
    };
    const CHAPTER_DENSITY = {
      "PSA": { "1": {...}, "2": {...}, ... },
      "PRO": { "1": {...}, ... },
      ...
    };
如果 index.html 已經在用舊版（只有詩篇時）的扁平結構
{en:[...], ja:[...]}，需要同步調整前端讀取的程式碼，
把 index.html 讀取資料那段程式碼貼給我，我可以幫忙改。
"""

import json
import os
import re
import csv
from collections import defaultdict

BIBLE_DATA_DIR = r"E:\bible-lang-app\bible_data"
BIBLE_TEXT_DIR = os.path.join(BIBLE_DATA_DIR, "bible_text")
OUTPUT_JS_PATH = r"E:\bible-lang-app\chunks_data.js"
DENSITY_CSV_PATH = os.path.join(BIBLE_DATA_DIR, "chapter_density_report.csv")

BOOK_ALIAS = {"psalms": "PSA"}
PATTERN = re.compile(r"^chunks_(en|ja)_([A-Za-z0-9]+)_(\d{3})-(\d{3})\.json$")


def resolve_book_code(book_slug):
    return BOOK_ALIAS.get(book_slug, book_slug.upper())


def scan_files():
    """回傳 {(lang, book_slug): [檔名, ...]}"""
    result = defaultdict(list)
    for fname in os.listdir(BIBLE_DATA_DIR):
        m = PATTERN.match(fname)
        if m:
            lang, book_slug = m.group(1), m.group(2)
            result[(lang, book_slug)].append(fname)
    for key in result:
        result[key].sort()
    return result


def load_entries(fnames):
    entries = []
    for fname in fnames:
        fpath = os.path.join(BIBLE_DATA_DIR, fname)
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            entries.extend(data)
        except Exception as e:
            print(f"警告：讀取 {fname} 失敗（{e}），已跳過。")
    return entries


def check_duplicates(entries, label):
    ids = [e.get("id", "") for e in entries]
    seen, dupes = set(), set()
    for i in ids:
        if i in seen:
            dupes.add(i)
        seen.add(i)
    if dupes:
        print(f"⚠️ 警告：{label} 發現重複id（共{len(dupes)}個）："
              f"{sorted(dupes)[:10]}{' ...' if len(dupes) > 10 else ''}")
        return False
    return True


def check_required_fields(entries, label, required):
    missing = [e.get("id", "?") for e in entries if not required.issubset(e.keys())]
    if missing:
        print(f"⚠️ 警告：{label} 有{len(missing)}條缺少必要欄位："
              f"{missing[:10]}{' ...' if len(missing) > 10 else ''}")
        return False
    return True


def get_verse_counts(book_slug):
    code = resolve_book_code(book_slug)
    path = os.path.join(BIBLE_TEXT_DIR, f"{code}.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {int(ch): len(chdata.get("verses", {})) for ch, chdata in data.get("chapters", {}).items()}


def compute_density(en_entries, ja_entries, verse_counts, total_chapters):
    en_by_ch, ja_by_ch = defaultdict(int), defaultdict(int)
    for e in en_entries:
        en_by_ch[e["chapter"]] += 1
    for e in ja_entries:
        ja_by_ch[e["chapter"]] += 1

    density = {}
    for ch in range(1, total_chapters + 1):
        verses = verse_counts.get(ch, 0)
        en_c, ja_c = en_by_ch.get(ch, 0), ja_by_ch.get(ch, 0)
        total = en_c + ja_c
        score = round(total / verses, 3) if verses else 0.0
        tier = "優先" if score >= 0.5 else "一般" if score >= 0.2 else "低優先"
        density[str(ch)] = {
            "chapter": ch, "verse_count": verses,
            "en_chunk_count": en_c, "ja_chunk_count": ja_c,
            "total_chunk_count": total, "density_score": score, "tier": tier,
        }
    return density


def main():
    files_by_key = scan_files()
    book_slugs = sorted(set(book for (_, book) in files_by_key.keys()))

    if not book_slugs:
        print("目前資料夾裡沒有任何符合格式的批次檔案，無法合併。")
        return

    all_chunks_data = {}
    all_density = {}
    all_ok = True
    grand_total = 0

    for book_slug in book_slugs:
        code = resolve_book_code(book_slug)
        en_files = files_by_key.get(("en", book_slug), [])
        ja_files = files_by_key.get(("ja", book_slug), [])

        en_entries = load_entries(en_files)
        ja_entries = load_entries(ja_files)

        print(f"=== {code}（{book_slug}） ===")
        print(f"英文：{len(en_files)}個檔案 → {len(en_entries)}條")
        print(f"日文：{len(ja_files)}個檔案 → {len(ja_entries)}條")

        en_id_ok = check_duplicates(en_entries, f"{code} 英文")
        ja_id_ok = check_duplicates(ja_entries, f"{code} 日文")
        en_field_ok = check_required_fields(
            en_entries, f"{code} 英文",
            {"id", "chapter", "verse", "text", "blank", "answer", "tag", "freq", "gloss", "ref", "usage"}
        )
        ja_field_ok = check_required_fields(
            ja_entries, f"{code} 日文",
            {"id", "chapter", "verse", "text", "reading", "blank", "answer", "tag", "freq", "gloss", "ref", "usage"}
        )
        all_ok = all_ok and en_id_ok and ja_id_ok and en_field_ok and ja_field_ok

        verse_counts = get_verse_counts(book_slug)
        total_chapters = max(verse_counts.keys()) if verse_counts else 0
        if total_chapters == 0:
            print(f"警告：找不到 {code}.json 或內容為空，密度計算略過。")

        density = compute_density(en_entries, ja_entries, verse_counts, total_chapters) if total_chapters else {}

        all_chunks_data[code] = {"en": en_entries, "ja": ja_entries}
        all_density[code] = density
        grand_total += len(en_entries) + len(ja_entries)
        print()

    # 寫出 chunks_data.js
    lines = [
        "// 自動產生檔案，請勿手動編輯 —— 執行 merge_chunks.py 重新產生",
        "// 多書卷版：CHUNKS_DATA / CHAPTER_DENSITY 都以書卷代號分層",
        "",
        "const CHUNKS_DATA = " + json.dumps(all_chunks_data, ensure_ascii=False, indent=2) + ";",
        "",
        "const CHAPTER_DENSITY = " + json.dumps(all_density, ensure_ascii=False, indent=2) + ";",
        "",
    ]
    with open(OUTPUT_JS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # 寫出密度CSV（含書卷欄位）
    with open(DENSITY_CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["book", "chapter", "verse_count", "en_chunk_count",
                          "ja_chunk_count", "total_chunk_count", "density_score", "tier"])
        for code, density in all_density.items():
            for ch_str, d in density.items():
                writer.writerow([code, d["chapter"], d["verse_count"], d["en_chunk_count"],
                                  d["ja_chunk_count"], d["total_chunk_count"],
                                  d["density_score"], d["tier"]])

    print(f"已產生：{OUTPUT_JS_PATH}")
    print(f"已產生：{DENSITY_CSV_PATH}")
    print()
    print(f"涵蓋書卷：{[resolve_book_code(b) for b in book_slugs]}")
    print(f"全書卷總計語塊數：{grand_total}")
    print(f"全部檢查通過：{all_ok}")


if __name__ == "__main__":
    main()

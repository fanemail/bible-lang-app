# -*- coding: utf-8 -*-
"""
全面體檢：一次檢查 bible_data 資料夾（及相關檔案）的真實現況，
不改動任何檔案，純粹產出報告，作為後續整頓的依據。

用法：
    C:\\Users\\freeman\\AppData\\Local\\Programs\\Python\\Python314\\python.exe audit_everything.py
"""
import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "bible_data")
BIBLE_TEXT_DIR = os.path.join(DATA_DIR, "bible_text")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")

BOOKS = [
    ("創世記","GEN",50), ("出埃及記","EXO",40), ("利未記","LEV",27), ("民數記","NUM",36),
    ("申命記","DEU",34), ("約書亞記","JOS",24), ("士師記","JDG",21), ("路得記","RUT",4),
    ("撒母耳記上","1SA",31), ("撒母耳記下","2SA",24), ("列王紀上","1KI",22), ("列王紀下","2KI",25),
    ("歷代志上","1CH",29), ("歷代志下","2CH",36), ("以斯拉記","EZR",10), ("尼希米記","NEH",13),
    ("以斯帖記","EST",10), ("約伯記","JOB",42), ("詩篇","PSA",150), ("箴言","PRO",31),
    ("傳道書","ECC",12), ("雅歌","SNG",8), ("以賽亞書","ISA",66), ("耶利米書","JER",52),
    ("耶利米哀歌","LAM",5), ("以西結書","EZK",48), ("但以理書","DAN",12), ("何西阿書","HOS",14),
    ("約珥書","JOL",3), ("阿摩司書","AMO",9), ("俄巴底亞書","OBA",1), ("約拿書","JON",4),
    ("彌迦書","MIC",7), ("那鴻書","NAM",3), ("哈巴谷書","HAB",3), ("西番雅書","ZEP",3),
    ("哈該書","HAG",2), ("撒迦利亞書","ZEC",14), ("瑪拉基書","MAL",4), ("馬太福音","MAT",28),
    ("馬可福音","MRK",16), ("路加福音","LUK",24), ("約翰福音","JHN",21), ("使徒行傳","ACT",28),
    ("羅馬書","ROM",16), ("哥林多前書","1CO",16), ("哥林多後書","2CO",13), ("加拉太書","GAL",6),
    ("以弗所書","EPH",6), ("腓立比書","PHP",4), ("歌羅西書","COL",4), ("帖撒羅尼迦前書","1TH",5),
    ("帖撒羅尼迦後書","2TH",3), ("提摩太前書","1TI",6), ("提摩太後書","2TI",4), ("提多書","TIT",3),
    ("腓利門書","PHM",1), ("希伯來書","HEB",13), ("雅各書","JAS",5), ("彼得前書","1PE",5),
    ("彼得後書","2PE",3), ("約翰一書","1JN",5), ("約翰二書","2JN",1), ("約翰三書","3JN",1),
    ("猶大書","JUD",1), ("啟示錄","REV",22),
]


def check_bible_text():
    print("=" * 60)
    print("一、bible_text/ 資料夾：66卷書逐一檢查")
    print("=" * 60)
    if not os.path.isdir(BIBLE_TEXT_DIR):
        print("  資料夾不存在！")
        return

    ok, corrupted, missing = [], [], []
    for zh_name, code, expected_ch in BOOKS:
        path = os.path.join(BIBLE_TEXT_DIR, f"{code}.json")
        if not os.path.exists(path):
            missing.append((code, zh_name))
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            corrupted.append((code, zh_name, f"JSON讀取失敗:{e}"))
            continue

        actual_ch = len(data.get("chapters", {}))
        total_v = empty_en = empty_zh = empty_ja = 0
        for ch_obj in data["chapters"].values():
            for v in ch_obj["verses"].values():
                total_v += 1
                if not v.get("en"): empty_en += 1
                if not v.get("zh"): empty_zh += 1
                if not v.get("ja"): empty_ja += 1

        if total_v == 0:
            corrupted.append((code, zh_name, "0節，空檔案"))
        elif empty_en == total_v or empty_zh == total_v:
            corrupted.append((code, zh_name, f"英/中文全空（共{total_v}節，缺en={empty_en}/缺zh={empty_zh}）"))
        elif actual_ch < expected_ch * 0.5:
            corrupted.append((code, zh_name, f"章數過少：{actual_ch}/{expected_ch}"))
        else:
            ok.append((code, zh_name, actual_ch, total_v))

    print(f"\n正常：{len(ok)}/66")
    print(f"損壞：{len(corrupted)}/66")
    print(f"缺檔：{len(missing)}/66")

    if corrupted:
        print("\n損壞清單：")
        for code, name, issue in corrupted:
            print(f"  [{code}] {name}：{issue}")
    if missing:
        print("\n缺檔清單：")
        for code, name in missing:
            print(f"  [{code}] {name}")


def check_psalms_duplicate():
    print("\n" + "=" * 60)
    print("二、詩篇資料是否有重複來源（psalms_full_output.json vs bible_text/PSA.json）")
    print("=" * 60)

    old_path = os.path.join(DATA_DIR, "psalms_full_output.json")
    new_path = os.path.join(BIBLE_TEXT_DIR, "PSA.json")

    old_exists = os.path.exists(old_path)
    new_exists = os.path.exists(new_path)
    print(f"  psalms_full_output.json 存在：{old_exists}")
    print(f"  bible_text/PSA.json 存在：{new_exists}")

    if old_exists and new_exists:
        with open(old_path, encoding="utf-8") as f:
            old_data = json.load(f)
        with open(new_path, encoding="utf-8") as f:
            new_data = json.load(f)

        old_verses = sum(len(c["verses"]) for c in old_data["chapters"].values())
        new_verses = sum(len(c["verses"]) for c in new_data["chapters"].values())
        print(f"  psalms_full_output.json：{len(old_data['chapters'])}章，{old_verses}節")
        print(f"  bible_text/PSA.json：{len(new_data['chapters'])}章，{new_verses}節")

        old_v1 = old_data["chapters"].get("1", {}).get("verses", {}).get("1", {})
        new_v1 = new_data["chapters"].get("1", {}).get("verses", {}).get("1", {})
        same = old_v1 == new_v1
        print(f"  第1章第1節內容是否一致：{same}")
        if not same:
            print(f"    psalms_full_output.json: {old_v1}")
            print(f"    bible_text/PSA.json: {new_v1}")

        print("\n  【結論】目前存在兩份詩篇資料，容易造成混淆，之後整頓時需要決定保留哪一份、")
        print("  並統一 index.html / psalms_data.js 的資料來源，不要兩邊並存。")


def check_vocab():
    print("\n" + "=" * 60)
    print("三、詞典檔案")
    print("=" * 60)
    path = os.path.join(DATA_DIR, "vocab_db.jsonl")
    if not os.path.exists(path):
        print("  vocab_db.jsonl 不存在！")
        return
    count = 0
    bad_ja = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            count += 1
            item = json.loads(line)
            ja = item.get("ja") or ""
            if "mymemory" in ja.lower() or "usagelimits" in ja.lower():
                bad_ja += 1
    print(f"  總詞數：{count}")
    print(f"  仍殘留MyMemory污染的詞數：{bad_ja}（應為0）")


def check_chunks():
    print("\n" + "=" * 60)
    print("四、語塊標注批次檔案")
    print("=" * 60)
    files = [f for f in os.listdir(DATA_DIR) if f.startswith("chunks_") and f.endswith(".json")] if os.path.isdir(DATA_DIR) else []
    if not files:
        print("  目前沒有任何 chunks_*.json 批次檔案（語塊標注尚未產出任何成果）")
    else:
        for f in sorted(files):
            path = os.path.join(DATA_DIR, f)
            with open(path, encoding="utf-8") as fp:
                data = json.load(fp)
            print(f"  {f}：{len(data)} 條語塊")

    chunks_data_js = os.path.join(BASE, "chunks_data.js")
    print(f"  chunks_data.js（合併後產物）存在：{os.path.exists(chunks_data_js)}")


def check_audio():
    print("\n" + "=" * 60)
    print("五、音頻檔案")
    print("=" * 60)
    for lang in ["en", "ja"]:
        d = os.path.join(AUDIO_DIR, lang, "PSA")
        if os.path.isdir(d):
            files = [f for f in os.listdir(d) if f.endswith(".mp3")]
            total_mb = sum(os.path.getsize(os.path.join(d, f)) for f in files) / 1024 / 1024
            print(f"  {lang}: {len(files)}/150 個檔案，共{total_mb:.1f}MB")
        else:
            print(f"  {lang}: 資料夾不存在")


def check_root_files():
    print("\n" + "=" * 60)
    print("六、根目錄關鍵檔案版本確認")
    print("=" * 60)
    targets = [
        ("index.html", None),
        ("vocab_data.js", None),
        ("psalms_data.js", None),
        ("chunks_data.js", None),
        ("download_bible_full.py", "偵測到舊檔案是壞資料"),
    ]
    for fname, marker in targets:
        path = os.path.join(BASE, fname)
        if not os.path.exists(path):
            print(f"  {fname}：不存在")
            continue
        size = os.path.getsize(path)
        info = f"存在，{size}bytes"
        if marker:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            has_marker = marker in content
            info += f"，{'是修正版' if has_marker else '⚠️仍是舊版！'}"
        print(f"  {fname}：{info}")


def main():
    check_bible_text()
    check_psalms_duplicate()
    check_vocab()
    check_chunks()
    check_audio()
    check_root_files()
    print("\n" + "=" * 60)
    print("體檢完畢。把以上完整輸出貼給AI，據此決定最終整頓方案。")
    print("=" * 60)


if __name__ == "__main__":
    main()

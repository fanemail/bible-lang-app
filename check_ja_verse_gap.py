# -*- coding: utf-8 -*-
"""
診斷腳本：逐章比對 timestamps/en/PSA 跟 timestamps/ja/PSA 的節數，
找出兩邊節數不一致的章節（英文節數是可信的基準，因為A1文字本身三語逐節對齊，
理論上每章節數應該完全相同，除非某章日文對齊有缺漏）。

用法：
  python check_ja_verse_gap.py
"""
import os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EN_DIR = os.path.join(BASE_DIR, "bible_data", "timestamps", "en", "PSA")
JA_DIR = os.path.join(BASE_DIR, "bible_data", "timestamps", "ja", "PSA")


def load_verse_count(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return len(data["verses"]), sorted(v["verse"] for v in data["verses"])


def main():
    if not os.path.isdir(EN_DIR) or not os.path.isdir(JA_DIR):
        print("找不到 en 或 ja 的 timestamps/PSA 資料夾，請確認路徑")
        return

    mismatches = []
    en_files = set(f for f in os.listdir(EN_DIR) if f.endswith(".json"))
    ja_files = set(f for f in os.listdir(JA_DIR) if f.endswith(".json"))

    missing_in_ja = sorted(en_files - ja_files)
    missing_in_en = sorted(ja_files - en_files)

    if missing_in_ja:
        print(f"⚠ 這些章節英文有檔案、日文完全沒有（{len(missing_in_ja)}個）：{missing_in_ja}")
    if missing_in_en:
        print(f"⚠ 這些章節日文有檔案、英文完全沒有（{len(missing_in_en)}個）：{missing_in_en}")

    common = sorted(en_files & ja_files)
    for fname in common:
        en_count, en_verses = load_verse_count(os.path.join(EN_DIR, fname))
        ja_count, ja_verses = load_verse_count(os.path.join(JA_DIR, fname))
        if en_count != ja_count:
            missing_verses = sorted(set(en_verses) - set(ja_verses))
            extra_verses = sorted(set(ja_verses) - set(en_verses))
            mismatches.append((fname, en_count, ja_count, missing_verses, extra_verses))

    if not mismatches:
        print("\n除了上面列出的整章缺失（如果有的話），其餘章節英文/日文節數完全一致。")
    else:
        print(f"\n找到{len(mismatches)}個章節節數對不上：")
        for fname, en_c, ja_c, missing, extra in mismatches:
            chapter = fname.replace(".json", "")
            print(f"  第{chapter}章：英文{en_c}節、日文{ja_c}節", end="")
            if missing:
                print(f"（日文缺少第{missing}節）", end="")
            if extra:
                print(f"（日文多出第{extra}節，不應該發生，需檢查）", end="")
            print()

    total_gap = sum(en_c - ja_c for _, en_c, ja_c, _, _ in mismatches)
    if missing_in_ja:
        total_gap += sum(load_verse_count(os.path.join(EN_DIR, f))[0] for f in missing_in_ja)
    print(f"\n總計節數差異：{total_gap}節（應該要對得上你剛才看到的 2461-2452=9 這個數字）")


if __name__ == "__main__":
    main()

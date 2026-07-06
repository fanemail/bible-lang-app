# -*- coding: utf-8 -*-
"""
時間戳「多詞共用同一起訖時間」異常診斷腳本。

背景：batch_align_psa.py／batch_align_psa_ja.py／run_alignment_queue.py對齊時，
difflib判定為「replace」的區段（WhisperX辨識文字跟資料庫正確經文對不上的部分），
目前的處理方式是把該區段內「所有」資料庫詞，全部指定成同一組「區段起點～區段訖點」
時間戳，而不是依詞數平均分配。這會導致同一時間戳被2個以上的詞共用，
物理上不可能（不同詞不可能同時發音），是真正的資料瑕疵。

影響：
- 若這種異常區塊剛好落在某節的「最後一個詞」，該節整節播放（verse_audio.js）的
  endTime會不準，可能造成整節播放放到一半就停（使用者回報的「只讀半句」）。
- 若異常區塊剛好落在某語塊的起訖詞上，該語塊播放（chunk_audio.js）範圍也會不準。

用法（3.14主環境，不需要whisperx_env）：
  python check_timestamp_collisions.py
"""
import os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIMESTAMPS_BASE_DIR = os.path.join(BASE_DIR, "bible_data", "timestamps")
LANGS = ["en", "ja"]


def find_collision_runs(words):
    """在一個詞清單裡找出「連續2個以上詞，startTime跟endTime完全相同」的區塊。
       回傳清單，每項是(run_start_wordIndex, run_end_wordIndex, start, end)。"""
    runs = []
    i = 0
    n = len(words)
    while i < n - 1:
        j = i
        while (j + 1 < n
               and words[j+1]["startTime"] == words[i]["startTime"]
               and words[j+1]["endTime"] == words[i]["endTime"]):
            j += 1
        if j > i:
            runs.append((words[i]["wordIndex"], words[j]["wordIndex"],
                          words[i]["startTime"], words[i]["endTime"]))
            i = j + 1
        else:
            i += 1
    return runs


def main():
    grand_total_verses = 0
    grand_affected_verses = 0
    grand_boundary_verses = 0  # 異常區塊觸及節邊界（第一個或最後一個詞）的節數，最嚴重

    for lang in LANGS:
        lang_dir = os.path.join(TIMESTAMPS_BASE_DIR, lang)
        if not os.path.isdir(lang_dir):
            print(f"{lang}：找不到 {lang_dir}，跳過")
            continue

        for book_code in sorted(os.listdir(lang_dir)):
            book_dir = os.path.join(lang_dir, book_code)
            if not os.path.isdir(book_dir):
                continue

            book_total_verses = 0
            book_affected_verses = 0
            book_boundary_verses = 0
            boundary_examples = []

            for fname in sorted(os.listdir(book_dir)):
                if not fname.endswith(".json"):
                    continue
                with open(os.path.join(book_dir, fname), encoding="utf-8") as f:
                    data = json.load(f)
                chapter = data["chapter"]

                for v in data["verses"]:
                    words = v["words"]
                    book_total_verses += 1
                    if not words:
                        continue
                    runs = find_collision_runs(words)
                    if not runs:
                        continue
                    book_affected_verses += 1

                    first_idx, last_idx = words[0]["wordIndex"], words[-1]["wordIndex"]
                    touches_boundary = any(
                        run_start <= first_idx <= run_end or run_start <= last_idx <= run_end
                        for run_start, run_end, _, _ in runs
                    )
                    if touches_boundary:
                        book_boundary_verses += 1
                        if len(boundary_examples) < 5:
                            boundary_examples.append((chapter, v["verse"], runs))

            grand_total_verses += book_total_verses
            grand_affected_verses += book_affected_verses
            grand_boundary_verses += book_boundary_verses

            if book_affected_verses > 0:
                pct = book_affected_verses / book_total_verses * 100
                boundary_pct = book_boundary_verses / book_total_verses * 100
                print(f"\n[{lang}/{book_code}] 共{book_total_verses}節，"
                      f"{book_affected_verses}節含異常時間戳區塊（{pct:.1f}%），"
                      f"其中{book_boundary_verses}節異常觸及節邊界（{boundary_pct:.1f}%，最嚴重）")
                for chapter, verse, runs in boundary_examples:
                    run_desc = "; ".join(f"詞{r[0]}~{r[1]}共用{r[2]}~{r[3]}秒" for r in runs)
                    print(f"    例：第{chapter}章第{verse}節 —— {run_desc}")
            else:
                print(f"\n[{lang}/{book_code}] 共{book_total_verses}節，未發現異常")

    print(f"\n{'='*60}")
    print(f"總計：{grand_total_verses}節，{grand_affected_verses}節含異常區塊"
          f"（{grand_affected_verses/grand_total_verses*100:.1f}%），"
          f"{grand_boundary_verses}節異常觸及邊界、影響播放起訖"
          f"（{grand_boundary_verses/grand_total_verses*100:.1f}%）")


if __name__ == "__main__":
    main()

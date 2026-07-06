# -*- coding: utf-8 -*-
"""
夜間排隊自動對齊腳本。

用途：一個指令，自動判斷「哪些書卷+哪個語言」還沒做過WhisperX對齊，排隊依序處理，
不需要每次手動改路徑常數、也不需要盯著螢幕決定下一步該跑哪個。

判斷「做完了沒」的依據：bible_data/timestamps/{語言}/{書卷}/ 底下的json檔案數量，
是不是等於該書卷的總章數。已經做完的書卷+語言組合會直接跳過（不重跑），
只處理還缺的部分——即使是同一本書缺最後幾章，也只會補那幾章，不會整本重來。

任何一章、一本書出錯，都會記錄下來、繼續跑下一個，不會讓整個排隊中斷一整晚的時間。

用法（whisperx_env環境）：
  cd E:\\bible-lang-app
  whisperx_env\\Scripts\\activate
  python run_alignment_queue.py

跑之前不需要準備任何東西——書卷清單、章數、路徑，腳本自己都知道，
只要 bible_data/audio/{en,ja}/{書卷}/ 底下有音頻檔案，腳本就會自動排進待辦清單。
"""
import json, re, os, time, difflib, traceback
import whisperx

BASE_DIR = r"E:\bible-lang-app"
BIBLE_TEXT_DIR = os.path.join(BASE_DIR, "bible_data", "bible_text")
AUDIO_BASE_DIR = os.path.join(BASE_DIR, "bible_data", "audio")
TIMESTAMPS_BASE_DIR = os.path.join(BASE_DIR, "bible_data", "timestamps")
DEVICE = "cpu"
ASR_MODEL_SIZE = "small"

# 書卷代碼 -> 總章數（跟download_audio_multi.py/index.html裡的登記表一致）
BOOK_CHAPTERS = {
    "PSA": 150, "PRO": 31, "ISA": 66, "ECC": 12, "GEN": 50,
    "MAT": 28, "MRK": 16, "LUK": 24, "JHN": 21, "REV": 22, "DAN": 12,
}
# 處理順序：同語言共用同一套模型，先把一個語言全部做完再換下一個，減少重複載入模型的時間
LANGS = ["en", "ja"]

EN_PUNCT_PATTERN = re.compile(r"[^a-zA-Z']")
JA_PUNCT_PATTERN = re.compile(
    r"[\s　、。，．・「」『』（）()\[\]【】〈〉《》"
    r"！？!?：:；;…—～〜\-\"'“”‘’]"
)


def normalize_en(w):
    return EN_PUNCT_PATTERN.sub("", w).lower()


def normalize_ja(ch):
    return JA_PUNCT_PATTERN.sub("", ch)


def build_ref_tokens(text, lang):
    """英文以空白分詞，日文沒有空白改成逐字，跟各自單語言版腳本的邏輯一致。"""
    if lang == "ja":
        return [{"word": ch, "norm": normalize_ja(ch)} for ch in text if normalize_ja(ch)]
    return [{"word": w, "norm": normalize_en(w)} for w in text.split()]


def get_remaining_chapters(lang, book_code):
    """回傳這個書卷+語言還缺哪些章節（用時間戳檔案存不存在來判斷），全部做完回傳空list。"""
    total = BOOK_CHAPTERS[book_code]
    output_dir = os.path.join(TIMESTAMPS_BASE_DIR, lang, book_code)
    return [ch for ch in range(1, total + 1)
            if not os.path.exists(os.path.join(output_dir, f"{ch:03d}.json"))]


def align_chapter(book_code, lang, ch_num, chapter_data, audio_dir, asr_model, align_model, metadata):
    audio_path = os.path.join(audio_dir, f"{ch_num:03d}.mp3")
    if not os.path.exists(audio_path):
        return None, "音頻檔案不存在"
    verses = chapter_data["verses"]
    verse_nums = sorted(verses.keys(), key=int)
    verse_list = [(vn, verses[vn][lang]) for vn in verse_nums if verses[vn].get(lang)]
    if not verse_list:
        return None, f"{lang}文字為空"

    ref_tokens = []
    for vn, text in verse_list:
        for tok in build_ref_tokens(text, lang):
            ref_tokens.append({"verse": vn, "word": tok["word"], "norm": tok["norm"]})

    audio = whisperx.load_audio(audio_path)
    asr_result = asr_model.transcribe(audio, language=lang)
    aligned = whisperx.align(
        asr_result["segments"], align_model, metadata,
        audio, DEVICE, return_char_alignments=False)
    asr_words = []
    for seg in aligned["segments"]:
        for w in seg.get("words", []):
            if "start" in w and "end" in w:
                asr_words.append(w)

    ref_norms = [t["norm"] for t in ref_tokens]
    normalize_fn = normalize_ja if lang == "ja" else normalize_en
    asr_norms = [normalize_fn(w.get("word", "")) for w in asr_words]
    matcher = difflib.SequenceMatcher(None, ref_norms, asr_norms, autojunk=False)
    for t in ref_tokens:
        t["start"] = None
        t["end"] = None
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for off in range(i2 - i1):
                ref_tokens[i1+off]["start"] = asr_words[j1+off].get("start")
                ref_tokens[i1+off]["end"] = asr_words[j1+off].get("end")
        elif tag == "replace":
            sl = asr_words[j1:j2]
            if sl:
                bs, be = sl[0].get("start"), sl[-1].get("end")
                for off in range(i2 - i1):
                    ref_tokens[i1+off]["start"] = bs
                    ref_tokens[i1+off]["end"] = be
    for i, t in enumerate(ref_tokens):
        if t["start"] is None:
            pe = next((ref_tokens[j]["end"] for j in range(i-1,-1,-1) if ref_tokens[j]["end"] is not None), None)
            ns = next((ref_tokens[j]["start"] for j in range(i+1,len(ref_tokens)) if ref_tokens[j]["start"] is not None), None)
            t["start"] = pe if pe is not None else ns
            t["end"] = ns if ns is not None else pe

    by_verse = {}
    for t in ref_tokens:
        by_verse.setdefault(t["verse"], []).append(t)
    output = {"book": book_code, "chapter": ch_num,
              "audioFile": f"{ch_num:03d}.mp3", "verses": []}
    for vn, text in verse_list:
        words = by_verse.get(vn, [])
        v_start = words[0]["start"] if words else None
        v_end = words[-1]["end"] if words else None
        entry_words = [{"wordIndex": i, "wordText": w["word"],
                        "startTime": w["start"], "endTime": w["end"]}
                       for i, w in enumerate(words)]
        output["verses"].append({"verse": int(vn), "text": text,
                                  "startTime": v_start, "endTime": v_end,
                                  "words": entry_words})
    unresolved = sum(1 for t in ref_tokens if t["start"] is None)
    unit = "字" if lang == "ja" else "詞"
    return output, f"OK | ASR={len(asr_words)}{unit} REF={len(ref_tokens)}{unit} 插值未解={unresolved}"


def process_book_lang(book_code, lang, remaining, asr_model, align_model, metadata, log):
    bible_text_path = os.path.join(BIBLE_TEXT_DIR, f"{book_code}.json")
    audio_dir = os.path.join(AUDIO_BASE_DIR, lang, book_code)
    output_dir = os.path.join(TIMESTAMPS_BASE_DIR, lang, book_code)
    total = BOOK_CHAPTERS[book_code]

    if not os.path.exists(bible_text_path):
        log.append(f"[{lang}/{book_code}] !! 找不到 {bible_text_path}，整卷跳過")
        return
    os.makedirs(output_dir, exist_ok=True)
    with open(bible_text_path, "r", encoding="utf-8") as f:
        chapters = json.load(f)["chapters"]

    print(f"\n{'='*50}\n[{lang}/{book_code}] 共{total}章，還剩{len(remaining)}章待處理")
    done = failed = 0
    for ch in remaining:
        ch_key = str(ch)
        if ch_key not in chapters:
            print(f"  [{ch:3d}/{total}] !! 文字資料庫中找不到第{ch}章，跳過")
            failed += 1
            continue
        t0 = time.time()
        print(f"  [{ch:3d}/{total}] 處理第{ch}章...", end=" ", flush=True)
        try:
            out_path = os.path.join(output_dir, f"{ch:03d}.json")
            result, msg = align_chapter(book_code, lang, ch, chapters[ch_key],
                                         audio_dir, asr_model, align_model, metadata)
            if result is None:
                print(f"跳過 | {msg}")
                failed += 1
            else:
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False)
                print(f"完成 {time.time()-t0:.0f}秒 | {msg}")
                done += 1
        except Exception as e:
            print(f"錯誤：{e}")
            traceback.print_exc()
            failed += 1
    log.append(f"[{lang}/{book_code}] 本次新完成{done}章，失敗{failed}章")


def main():
    print("掃描還有哪些「書卷+語言」組合尚未完成對齊...")
    queue = []
    for lang in LANGS:
        audio_lang_dir = os.path.join(AUDIO_BASE_DIR, lang)
        if not os.path.isdir(audio_lang_dir):
            continue
        for book_code in sorted(os.listdir(audio_lang_dir)):
            if book_code in BOOK_CHAPTERS and os.path.isdir(os.path.join(audio_lang_dir, book_code)):
                queue.append((lang, book_code))

    log = []
    failed_langs = set()
    current_lang = None
    asr_model = align_model = metadata = None
    total_start = time.time()

    for lang, book_code in queue:
        if lang in failed_langs:
            continue
        remaining = get_remaining_chapters(lang, book_code)
        if not remaining:
            print(f"[{lang}/{book_code}] 已全部完成（{BOOK_CHAPTERS[book_code]}章），跳過")
            continue

        if lang != current_lang:
            print(f"\n載入{lang}語言的ASR/對齊模型（只需載入一次）...")
            try:
                asr_model = whisperx.load_model(ASR_MODEL_SIZE, DEVICE, compute_type="float32")
                align_model, metadata = whisperx.load_align_model(language_code=lang, device=DEVICE)
            except Exception as e:
                log.append(f"[{lang}] !! 模型載入失敗，這個語言剩下的書卷全部跳過：{e}")
                failed_langs.add(lang)
                continue
            current_lang = lang

        process_book_lang(book_code, lang, remaining, asr_model, align_model, metadata, log)

    total_elapsed = time.time() - total_start
    print(f"\n{'='*50}\n全部排隊處理完畢。總耗時{total_elapsed/3600:.1f}小時\n")
    print("本次執行總結：")
    if log:
        for line in log:
            print(f"  {line}")
    else:
        print("  沒有新工作（全部書卷+語言都已經完成，或還沒下載音頻）")


if __name__ == "__main__":
    main()

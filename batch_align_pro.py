# -*- coding: utf-8 -*-
import json, re, os, time, difflib, traceback
import whisperx

BIBLE_TEXT_PATH = r"E:\bible-lang-app\bible_data\bible_text\PRO.json"
AUDIO_DIR       = r"E:\bible-lang-app\bible_data\audio\en\PRO"
OUTPUT_DIR      = r"E:\bible-lang-app\bible_data\timestamps\en\PRO"
TOTAL_CHAPTERS  = 31
BOOK_CODE       = "PRO"
DEVICE          = "cpu"
LANGUAGE        = "en"
ASR_MODEL_SIZE  = "small"

def normalize(w):
    return re.sub(r"[^a-zA-Z']", "", w).lower()

def align_chapter(ch_num, chapter_data, asr_model, align_model, metadata):
    audio_path = os.path.join(AUDIO_DIR, f"{ch_num:03d}.mp3")
    if not os.path.exists(audio_path):
        return None, "音頻檔案不存在"
    verses = chapter_data["verses"]
    verse_nums = sorted(verses.keys(), key=int)
    verse_list = [(vn, verses[vn]["en"]) for vn in verse_nums if verses[vn].get("en")]
    if not verse_list:
        return None, "英文文字為空"
    ref_tokens = []
    for vn, text in verse_list:
        for w in text.split():
            ref_tokens.append({"verse": vn, "word": w, "norm": normalize(w)})
    audio = whisperx.load_audio(audio_path)
    asr_result = asr_model.transcribe(audio, language=LANGUAGE)
    aligned = whisperx.align(
        asr_result["segments"], align_model, metadata,
        audio, DEVICE, return_char_alignments=False)
    asr_words = []
    for seg in aligned["segments"]:
        for w in seg.get("words", []):
            if "start" in w and "end" in w:
                asr_words.append(w)
    ref_norms = [t["norm"] for t in ref_tokens]
    asr_norms = [normalize(w.get("word", "")) for w in asr_words]
    matcher = difflib.SequenceMatcher(None, ref_norms, asr_norms, autojunk=False)
    opcodes = matcher.get_opcodes()
    for t in ref_tokens:
        t["start"] = None
        t["end"] = None
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            for off in range(i2 - i1):
                ref_tokens[i1+off]["start"] = asr_words[j1+off].get("start")
                ref_tokens[i1+off]["end"]   = asr_words[j1+off].get("end")
        elif tag == "replace":
            sl = asr_words[j1:j2]
            if sl:
                bs, be = sl[0].get("start"), sl[-1].get("end")
                for off in range(i2 - i1):
                    ref_tokens[i1+off]["start"] = bs
                    ref_tokens[i1+off]["end"]   = be
    for i, t in enumerate(ref_tokens):
        if t["start"] is None:
            pe = next((ref_tokens[j]["end"] for j in range(i-1,-1,-1) if ref_tokens[j]["end"] is not None), None)
            ns = next((ref_tokens[j]["start"] for j in range(i+1,len(ref_tokens)) if ref_tokens[j]["start"] is not None), None)
            t["start"] = pe if pe is not None else ns
            t["end"]   = ns if ns is not None else pe
    by_verse = {}
    for t in ref_tokens:
        by_verse.setdefault(t["verse"], []).append(t)
    output = {"book": BOOK_CODE, "chapter": ch_num,
              "audioFile": f"{ch_num:03d}.mp3", "verses": []}
    for vn, text in verse_list:
        words = by_verse.get(vn, [])
        v_start = words[0]["start"] if words else None
        v_end   = words[-1]["end"]  if words else None
        entry_words = [{"wordIndex": i, "wordText": w["word"],
                        "startTime": w["start"], "endTime": w["end"]}
                       for i, w in enumerate(words)]
        output["verses"].append({"verse": int(vn), "text": text,
                                  "startTime": v_start, "endTime": v_end,
                                  "words": entry_words})
    unresolved = sum(1 for t in ref_tokens if t["start"] is None)
    return output, f"OK | ASR={len(asr_words)}詞 REF={len(ref_tokens)}詞 插值未解={unresolved}"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"讀取{BOOK_CODE}文字資料庫...")
    with open(BIBLE_TEXT_PATH, "r", encoding="utf-8") as f:
        chapters = json.load(f)["chapters"]
    total = TOTAL_CHAPTERS
    print(f"共{total}章待處理")
    print(f"載入ASR模型({ASR_MODEL_SIZE})和對齊模型（只載入一次，請稍候）...")
    asr_model   = whisperx.load_model(ASR_MODEL_SIZE, DEVICE, compute_type="float32")
    align_model, metadata = whisperx.load_align_model(language_code=LANGUAGE, device=DEVICE)
    print("模型載入完畢，開始批次對齊。\n")
    done = skipped = failed = 0
    total_start = time.time()
    for ch in range(1, total + 1):
        out_path = os.path.join(OUTPUT_DIR, f"{ch:03d}.json")
        if os.path.exists(out_path):
            print(f"[{ch:3d}/{total}] 跳過（已存在）：{ch:03d}.json")
            skipped += 1
            continue
        ch_key = str(ch)
        if ch_key not in chapters:
            print(f"[{ch:3d}/{total}] !! 文字資料庫中找不到第{ch}章，跳過")
            failed += 1
            continue
        t0 = time.time()
        print(f"[{ch:3d}/{total}] 處理第{ch}章...", end=" ", flush=True)
        try:
            result, msg = align_chapter(ch, chapters[ch_key], asr_model, align_model, metadata)
            if result is None:
                print(f"跳過 | {msg}")
                failed += 1
            else:
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False)
                elapsed = time.time() - t0
                print(f"完成 {elapsed:.0f}秒 | {msg}")
                done += 1
        except Exception as e:
            print(f"錯誤：{e}")
            traceback.print_exc()
            failed += 1
    total_elapsed = time.time() - total_start
    print(f"\n全部完成。耗時{total_elapsed/3600:.1f}小時")
    print(f"成功:{done}  跳過:{skipped}  失敗:{failed}")
    print(f"輸出目錄：{OUTPUT_DIR}")

if __name__ == "__main__":
    main()

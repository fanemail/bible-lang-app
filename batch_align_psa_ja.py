# -*- coding: utf-8 -*-
"""
日文版WhisperX批次對齊腳本，架構完全比照英文版batch_align_psa.py，主要差異：

1. LANGUAGE = "ja"，用WhisperX內建的日文強制對齊模型
   （jonatasgrosman/wav2vec2-large-xlsr-53-japanese）。
2. 日文沒有空白分詞，所以比對的最小單位從「單詞」改成「單字」：
   英文版用 text.split() 把一節拆成一個個空白分開的單詞；
   日文版改成把一節拆成一個個獨立的字（逐字比對），
   這跟WhisperX原始碼裡「LANGUAGES_WITHOUT_SPACES = ['ja','zh']」的內部設計是一致的邏輯。
3. 輸出格式跟英文版完全相同（book/chapter/audioFile/verses[].startTime/endTime/words[]），
   只是words[]裡每個"word"其實是單一個日文字，供之後如果也想做日文語塊查表時使用；
   目前主要目標是verses[]裡的整節startTime/endTime（給build_verse_audio.py用）。

★重要提醒（跟英文版不同，請務必先讀）：
- 這是全新、還沒驗證過的組合（日文語音對齊本身在WhisperX裡沒有像英文那麼成熟），
  建議先用TEST_CHAPTERS限定跑2-3章測試品質，確認"插值未解"數字低、且輸出的
  startTime/endTime聽起來準，再放心跑完整150章。
- 如果一開始就跳出「找不到對齊模型」的錯誤，代表Hugging Face上那個日文模型當下抓不到
  （這是已知會發生的情況，不是你電腦的問題），請把完整錯誤訊息回報，需要另外換一個
  日文wav2vec2模型手動指定，不是這份腳本能自動解決的。

用法（whisperx_env環境，跟英文版一樣）：
  cd E:\\bible-lang-app
  whisperx_env\\Scripts\\activate
  python batch_align_psa_ja.py
"""
import json, re, os, time, difflib, traceback
import whisperx

BIBLE_TEXT_PATH = r"E:\bible-lang-app\bible_data\bible_text\PSA.json"
AUDIO_DIR       = r"E:\bible-lang-app\bible_data\audio\ja\PSA"
OUTPUT_DIR      = r"E:\bible-lang-app\bible_data\timestamps\ja\PSA"
DEVICE          = "cpu"
LANGUAGE        = "ja"
ASR_MODEL_SIZE  = "small"

# ★先用小數字測試品質！確認OK後再改成150跑全部（開頭幾章音頻通常較短，測試起來比較快）。
TEST_CHAPTERS   = 150

# 日文標點與空白，比對時要先拿掉，只留下真正有意義的字（漢字/假名）
JA_PUNCT_PATTERN = re.compile(
    r"[\s　、。，．・「」『』（）()\[\]【】〈〉《》"
    r"！？!?：:；;…—～〜\-\"'“”‘’]"
)

def normalize(ch):
    """日文版正規化：拿掉標點符號、全形/半形空白，不需要像英文那樣轉小寫（日文沒有大小寫）。"""
    return JA_PUNCT_PATTERN.sub("", ch)

def split_into_chars(text):
    """把一節日文文字拆成一個個字（逐字），拿掉標點符號後只留下有意義的字元。
       這是跟英文版text.split()對應的日文版本，因為日文沒有空白可以分詞。"""
    return [ch for ch in text if normalize(ch)]

def align_chapter(ch_num, chapter_data, asr_model, align_model, metadata):
    audio_path = os.path.join(AUDIO_DIR, f"{ch_num:03d}.mp3")
    if not os.path.exists(audio_path):
        return None, "音頻檔案不存在"
    verses = chapter_data["verses"]
    verse_nums = sorted(verses.keys(), key=int)
    verse_list = [(vn, verses[vn]["ja"]) for vn in verse_nums if verses[vn].get("ja")]
    if not verse_list:
        return None, "日文文字為空"

    # 逐字建立參考序列（對應英文版的逐詞ref_tokens，只是最小單位換成「字」）
    ref_tokens = []
    for vn, text in verse_list:
        for ch in split_into_chars(text):
            ref_tokens.append({"verse": vn, "word": ch, "norm": ch})

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
    output = {"book": "PSA", "chapter": ch_num,
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
    return output, f"OK | ASR={len(asr_words)}字 REF={len(ref_tokens)}字 插值未解={unresolved}"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("讀取詩篇文字資料庫...")
    with open(BIBLE_TEXT_PATH, "r", encoding="utf-8") as f:
        chapters = json.load(f)["chapters"]
    total = TEST_CHAPTERS
    print(f"共{total}章待處理（若這是測試批次，記得跑完後改TEST_CHAPTERS=150再跑全部）")
    print(f"載入ASR模型({ASR_MODEL_SIZE})和日文對齊模型（只載入一次，請稍候）...")
    asr_model = whisperx.load_model(ASR_MODEL_SIZE, DEVICE, compute_type="float32")
    try:
        align_model, metadata = whisperx.load_align_model(language_code=LANGUAGE, device=DEVICE)
    except Exception as e:
        print("\n!! 日文對齊模型載入失敗，這不是你電腦的問題，是WhisperX預設的日文模型")
        print("   （jonatasgrosman/wav2vec2-large-xlsr-53-japanese）當下在Hugging Face上抓不到。")
        print(f"   錯誤訊息：{e}\n")
        print("   請把這整段錯誤訊息回報，需要另外指定一個可用的日文wav2vec2模型，")
        print("   不是這份腳本能自動解決的，先停在這裡不會浪費時間去跑後面的章節。")
        return
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

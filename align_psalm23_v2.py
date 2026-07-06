# -*- coding: utf-8 -*-
import json
import re
import difflib
import whisperx

AUDIO_PATH = r"E:\bible-lang-app\bible_data\audio\en\PSA\023.mp3"
BIBLE_TEXT_PATH = r"E:\bible-lang-app\bible_data\bible_text\PSA.json"
OUTPUT_PATH = r"E:\bible-lang-app\bible_data\PSA_023_en_word_timestamps.json"
CHAPTER = "23"
DEVICE = "cpu"
LANGUAGE = "en"
ASR_MODEL_SIZE = "small"

def normalize(word):
    return re.sub(r"[^a-zA-Z']", "", word).lower()

def load_chapter_text(bible_text_path, chapter):
    with open(bible_text_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    verses = data["chapters"][chapter]["verses"]
    verse_nums = sorted(verses.keys(), key=lambda x: int(x))
    return [(vn, verses[vn]["en"]) for vn in verse_nums]

def build_reference_tokens(verse_list):
    tokens = []
    for vn, text in verse_list:
        for w in text.split():
            tokens.append({"verse": vn, "word": w, "norm": normalize(w)})
    return tokens

def main():
    print("讀取詩篇23篇正確經文...")
    verse_list = load_chapter_text(BIBLE_TEXT_PATH, CHAPTER)
    ref_tokens = build_reference_tokens(verse_list)
    print(f"共{len(verse_list)}節，資料庫文字共{len(ref_tokens)}詞")

    print("讀取音頻...")
    audio = whisperx.load_audio(AUDIO_PATH)

    print(f"載入whisper「{ASR_MODEL_SIZE}」模型進行完整轉錄（第一次會下載，較tiny準確）...")
    asr_model = whisperx.load_model(ASR_MODEL_SIZE, DEVICE, compute_type="float32")
    asr_result = asr_model.transcribe(audio, language=LANGUAGE)
    print("轉錄完成，開始精確逐詞對齊...")

    align_model, metadata = whisperx.load_align_model(language_code=LANGUAGE, device=DEVICE)
    aligned = whisperx.align(asr_result["segments"], align_model, metadata, audio, DEVICE,
                              return_char_alignments=False)

    asr_words = []
    for seg in aligned["segments"]:
        for w in seg.get("words", []):
            if "start" in w and "end" in w:
                asr_words.append(w)
    print(f"WhisperX實際辨識並對齊了{len(asr_words)}個詞（含篇名朗讀等，比資料庫的{len(ref_tokens)}詞多是正常的）")

    ref_norms = [t["norm"] for t in ref_tokens]
    asr_norms = [normalize(w.get("word", "")) for w in asr_words]

    print("進行文字比對，把時間戳對應回正確經文...")
    matcher = difflib.SequenceMatcher(None, ref_norms, asr_norms, autojunk=False)
    opcodes = matcher.get_opcodes()

    for t in ref_tokens:
        t["start"] = None
        t["end"] = None

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            for offset in range(i2 - i1):
                ref_tokens[i1 + offset]["start"] = asr_words[j1 + offset].get("start")
                ref_tokens[i1 + offset]["end"] = asr_words[j1 + offset].get("end")
        elif tag == "replace":
            asr_slice = asr_words[j1:j2]
            if asr_slice:
                block_start = asr_slice[0].get("start")
                block_end = asr_slice[-1].get("end")
                for offset in range(i2 - i1):
                    ref_tokens[i1 + offset]["start"] = block_start
                    ref_tokens[i1 + offset]["end"] = block_end

    for i, t in enumerate(ref_tokens):
        if t["start"] is None:
            prev_end = None
            for j in range(i - 1, -1, -1):
                if ref_tokens[j]["end"] is not None:
                    prev_end = ref_tokens[j]["end"]
                    break
            next_start = None
            for j in range(i + 1, len(ref_tokens)):
                if ref_tokens[j]["start"] is not None:
                    next_start = ref_tokens[j]["start"]
                    break
            if prev_end is not None and next_start is not None:
                t["start"] = prev_end
                t["end"] = next_start
            elif prev_end is not None:
                t["start"] = prev_end
                t["end"] = prev_end
            elif next_start is not None:
                t["start"] = next_start
                t["end"] = next_start

    output = {"book": "PSA", "chapter": int(CHAPTER), "audioFile": "023.mp3", "verses": []}
    by_verse = {}
    for t in ref_tokens:
        by_verse.setdefault(t["verse"], []).append(t)

    print("\n=== 每節時間戳摘要（請核對是否合理遞增、不重疊） ===")
    unresolved = 0
    for vn, text in verse_list:
        words = by_verse.get(vn, [])
        entry_words = []
        for i, w in enumerate(words):
            if w["start"] is None:
                unresolved += 1
            entry_words.append({"wordIndex": i, "wordText": w["word"],
                                 "startTime": w["start"], "endTime": w["end"]})
        v_start = words[0]["start"] if words else None
        v_end = words[-1]["end"] if words else None
        print(f"  第{vn}節 [{v_start}-{v_end}]：{text}")
        output["verses"].append({"verse": int(vn), "text": text,
                                  "startTime": v_start, "endTime": v_end,
                                  "words": entry_words})

    if unresolved:
        print(f"\n注意：有{unresolved}個詞完全找不到時間戳（前後都沒有可插值的鄰居），需要人工檢查")
    else:
        print("\n所有詞都成功取得時間戳（含插值補上的）")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n完成！結果已存到：{OUTPUT_PATH}")

if __name__ == "__main__":
    main()

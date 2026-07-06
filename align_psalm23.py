# -*- coding: utf-8 -*-
import json
import subprocess
import whisperx

# ---------- 設定區：路徑如果跟實際檔案位置不同，改這裡 ----------
BIBLE_TEXT_PATH = r"E:\bible-lang-app\bible_data\bible_text\PSA.json"
AUDIO_PATH = r"E:\bible-lang-app\bible_data\audio\en\PSA\023.mp3"
OUTPUT_PATH = r"E:\bible-lang-app\bible_data\PSA_023_en_word_timestamps.json"
CHAPTER = "23"
DEVICE = "cpu"
LANGUAGE = "en"
# ----------------------------------------------------------------

def get_audio_duration(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", path]
    out = subprocess.check_output(cmd).decode().strip()
    return float(out)

def load_chapter_text(bible_text_path, chapter):
    with open(bible_text_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    verses = data["chapters"][chapter]["verses"]
    verse_nums = sorted(verses.keys(), key=lambda x: int(x))
    return {vn: verses[vn]["en"] for vn in verse_nums}

def main():
    print("讀取詩篇23篇英文經文...")
    verse_texts = load_chapter_text(BIBLE_TEXT_PATH, CHAPTER)
    full_text = " ".join(verse_texts[vn] for vn in verse_texts)
    total_input_words = len(full_text.split())
    print(f"共{len(verse_texts)}節，全文約{total_input_words}詞")

    print("讀取音頻長度...")
    duration = get_audio_duration(AUDIO_PATH)
    print(f"音頻長度：{duration:.1f}秒")

    print("載入音頻...")
    audio = whisperx.load_audio(AUDIO_PATH)

    print("載入WhisperX英文對齊模型（第一次執行會下載模型，約1GB，請耐心等待）...")
    model_a, metadata = whisperx.load_align_model(language_code=LANGUAGE, device=DEVICE)

    segments = [{"start": 0.0, "end": duration, "text": full_text}]

    print("執行強制對齊（請耐心等待）...")
    result = whisperx.align(segments, model_a, metadata, audio, DEVICE,
                             return_char_alignments=False)

    aligned_words = result["segments"][0]["words"]
    print(f"對齊完成，取得{len(aligned_words)}個詞的時間戳（原文共{total_input_words}詞）")
    if len(aligned_words) != total_input_words:
        print("注意：對齊後詞數跟原文詞數不一致，之後需要人工核對分節是否正確。")

    output = {"book": "PSA", "chapter": int(CHAPTER), "audioFile": "023.mp3", "verses": []}
    word_cursor = 0
    for vn in verse_texts:
        n = len(verse_texts[vn].split())
        verse_words = aligned_words[word_cursor: word_cursor + n]
        word_cursor += n
        entry = {
            "verse": int(vn),
            "text": verse_texts[vn],
            "startTime": verse_words[0].get("start") if verse_words else None,
            "endTime": verse_words[-1].get("end") if verse_words else None,
            "words": [
                {"wordIndex": i, "wordText": w.get("word"),
                 "startTime": w.get("start"), "endTime": w.get("end")}
                for i, w in enumerate(verse_words)
            ]
        }
        output["verses"].append(entry)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"完成！結果已存到：{OUTPUT_PATH}")

if __name__ == "__main__":
    main()

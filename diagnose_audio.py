# -*- coding: utf-8 -*-
import json
import whisperx

AUDIO_PATH = r"E:\bible-lang-app\bible_data\audio\en\PSA\023.mp3"
BIBLE_TEXT_PATH = r"E:\bible-lang-app\bible_data\bible_text\PSA.json"
CHAPTER = "23"
DEVICE = "cpu"

def load_chapter_text(bible_text_path, chapter):
    with open(bible_text_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    verses = data["chapters"][chapter]["verses"]
    verse_nums = sorted(verses.keys(), key=lambda x: int(x))
    return {vn: verses[vn]["en"] for vn in verse_nums}

def main():
    print("讀取音頻...")
    audio = whisperx.load_audio(AUDIO_PATH)
    print(f"whisperx讀到的音頻樣本數：{len(audio)}，換算秒數：{len(audio)/16000:.1f}秒")

    print("載入whisper小型模型做實際語音辨識（純檢查用，不是最終流程）...")
    model = whisperx.load_model("tiny", DEVICE, compute_type="float32")
    result = model.transcribe(audio, language="en")

    print("=== Whisper實際聽到的內容 ===")
    for seg in result["segments"]:
        print(f"[{seg['start']:.1f}-{seg['end']:.1f}] {seg['text']}")

    print()
    print("=== 對照：詩篇23篇正確經文（前3節） ===")
    verse_texts = load_chapter_text(BIBLE_TEXT_PATH, CHAPTER)
    for vn in list(verse_texts.keys())[:3]:
        print(f"{vn}: {verse_texts[vn]}")

if __name__ == "__main__":
    main()

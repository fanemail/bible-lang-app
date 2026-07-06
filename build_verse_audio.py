# -*- coding: utf-8 -*-
"""
整節（整句）真人語音查表腳本（v2：新增日文支援）。

跟語塊查表（build_chunk_audio.py）不同，這裡完全不需要文字比對——WhisperX批次對齊
（batch_align_psa.py / batch_align_psa_ja.py）輸出的時間戳json裡，每一節本來就已經有
自己的startTime/endTime（對齊當下就算好了），這個腳本只是單純把它們撈出來、
整理成前端方便查詢的格式。

★v2變更：key格式從舊版的「書卷-章-節」（例如"PSA-23-4"）改成「書卷-語言-章-節」
（例如"PSA-en-23-4"、"PSA-ja-23-4"）。
原因：舊版key沒有語言區分，一旦日文資料也產生了，會跟英文用同一個key互相覆蓋
（後處理的語言會蓋掉先處理的），導致其中一種語言的整節播放資料整批消失。
改成含語言的key之後，中英日才能同時並存互不影響。

★注意：這是一個「破壞性格式變更」——index.html裡原本查VERSE_AUDIO的地方，
key組法也要跟著從"{書卷}-{章}-{節}"改成"{書卷}-{語言}-{章}-{節}"，
兩邊格式要對得起來，這支腳本才會真正生效，請務必同步確認index.html那端的改動。

輸入：bible_data/timestamps/en/{BOOK}/*.json、bible_data/timestamps/ja/{BOOK}/*.json
輸出：verse_audio.js —— 全域變數 VERSE_AUDIO，格式：
  {
    "PSA-en-23-4": { "book":"PSA","lang":"en","chapter":23,"verse":4,
                      "audioFile":"023.mp3","startTime":18.2,"endTime":28.0 },
    "PSA-ja-23-4": { "book":"PSA","lang":"ja","chapter":23,"verse":4,
                      "audioFile":"023.mp3","startTime":17.9,"endTime":27.5 }
  }
  前端用「目前語言-目前書卷-目前章-節號」組出key去查表即可。

用法（3.14主環境，不需要whisperx_env）：
  python build_verse_audio.py
"""
import os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIMESTAMPS_BASE_DIR = os.path.join(BASE_DIR, "bible_data", "timestamps")
OUTPUT_JS = os.path.join(BASE_DIR, "verse_audio.js")

LANGS = ["en", "ja"]


def main():
    verse_audio = {}

    if not os.path.isdir(TIMESTAMPS_BASE_DIR):
        print(f"!! 找不到 {TIMESTAMPS_BASE_DIR}，請確認WhisperX批次對齊有沒有跑過")
        return

    for lang in LANGS:
        lang_dir = os.path.join(TIMESTAMPS_BASE_DIR, lang)
        if not os.path.isdir(lang_dir):
            print(f"{lang}：找不到 {lang_dir}，跳過（這個語言還沒有WhisperX對齊產出）")
            continue

        for book_code in sorted(os.listdir(lang_dir)):
            book_dir = os.path.join(lang_dir, book_code)
            if not os.path.isdir(book_dir):
                continue
            chapter_count = 0
            verse_count = 0
            for fname in sorted(os.listdir(book_dir)):
                if not fname.endswith(".json"):
                    continue
                with open(os.path.join(book_dir, fname), encoding="utf-8") as f:
                    data = json.load(f)
                chapter = data["chapter"]
                audio_file = data.get("audioFile", fname.replace(".json", ".mp3"))
                for v in data["verses"]:
                    key = f'{book_code}-{lang}-{chapter}-{v["verse"]}'
                    verse_audio[key] = {
                        "book": book_code, "lang": lang, "chapter": chapter, "verse": v["verse"],
                        "audioFile": audio_file,
                        "startTime": round(v["startTime"], 3),
                        "endTime": round(v["endTime"], 3),
                    }
                    verse_count += 1
                chapter_count += 1
            print(f"{lang}/{book_code}：{chapter_count}章、{verse_count}節")

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("// 自動產生檔案，請勿手動編輯 —— 執行 build_verse_audio.py 重新產生\n")
        f.write("// 整節真人語音時間戳查表（直接來自WhisperX對齊結果，無需文字比對）\n")
        f.write("// key格式：{書卷}-{語言}-{章}-{節}，例如 PSA-ja-23-4\n\n")
        f.write("const VERSE_AUDIO = ")
        json.dump(verse_audio, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    en_count = sum(1 for v in verse_audio.values() if v["lang"] == "en")
    ja_count = sum(1 for v in verse_audio.values() if v["lang"] == "ja")
    print(f"\n完成：共{len(verse_audio)}節（英文{en_count}節、日文{ja_count}節），寫入 {OUTPUT_JS}")


if __name__ == "__main__":
    main()

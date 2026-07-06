# -*- coding: utf-8 -*-
"""
日文對齊測試抽查工具：直接讀取bible_data/timestamps/ja/PSA/00X.json（WhisperX剛對齊出來的原始
時間戳檔案），把裡面每一節剪成一個個小mp3片段，方便你雙擊聽,先確認品質再決定要不要跑完150章。

跟extract_chunk_clips.py不同的地方：這裡不需要先跑verse_audio.js查表，直接讀原始時間戳json，
因為現在只是要測試前3章的品質，還沒有需要正式的查表格式。

用法：
  python preview_ja_verses.py 1        剪第1章全部節
  python preview_ja_verses.py 1 2 3    剪第1、2、3章全部節
"""
import os, re, json, subprocess, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIMESTAMPS_DIR = os.path.join(BASE_DIR, "bible_data", "timestamps", "ja", "PSA")
AUDIO_DIR = os.path.join(BASE_DIR, "bible_data", "audio", "ja", "PSA")
OUTPUT_DIR = os.path.join(BASE_DIR, "ja_verse_preview")
PADDING = 0.5


def safe_filename(s, max_len=30):
    s = re.sub(r'[\\/:*?"<>|]', "", s)
    return s.strip()[:max_len]


def extract_clip(audio_file, start, end, out_path, padding=0.0):
    s = max(0, start - padding)
    duration = (end - start) + 2 * padding
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", audio_file, "-ss", f"{s:.3f}", "-t", f"{duration:.3f}",
        "-acodec", "libmp3lame", out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr


def main():
    chapters = [int(a) for a in sys.argv[1:]] or [1]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ok = fail = 0
    for ch in chapters:
        ts_path = os.path.join(TIMESTAMPS_DIR, f"{ch:03d}.json")
        if not os.path.exists(ts_path):
            print(f"!! 找不到 {ts_path}，這章可能還沒對齊")
            continue
        with open(ts_path, encoding="utf-8") as f:
            data = json.load(f)
        audio_file = os.path.join(AUDIO_DIR, data.get("audioFile", f"{ch:03d}.mp3"))
        if not os.path.exists(audio_file):
            print(f"!! 找不到音頻檔案 {audio_file}")
            continue
        print(f"第{ch}章（共{len(data['verses'])}節）：")
        for v in data["verses"]:
            if v["startTime"] is None or v["endTime"] is None:
                print(f"  !! 第{v['verse']}節沒有時間戳，跳過")
                fail += 1
                continue
            label = safe_filename(v["text"])
            out_path = os.path.join(OUTPUT_DIR, f"PSA{ch:03d}v{v['verse']:03d}_{label}.mp3")
            success, err = extract_clip(audio_file, v["startTime"], v["endTime"], out_path, PADDING)
            if success:
                print(f"  ✓ 第{v['verse']}節（{v['text'][:20]}...）")
                ok += 1
            else:
                print(f"  !! 第{v['verse']}節剪輯失敗：{err}")
                fail += 1
    print(f"\n完成：{ok}節成功，{fail}節失敗")
    print(f"檔案存在：{OUTPUT_DIR}，雙擊mp3檔案即可播放")


if __name__ == "__main__":
    main()

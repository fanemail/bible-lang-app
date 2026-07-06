# -*- coding: utf-8 -*-
"""
語塊音頻抽查工具：把chunk_audio.js裡指定的幾條語塊，從整章音頻裡剪成一個個獨立的
小mp3檔案，存到 chunk_audio_preview 資料夾。剪好之後，直接在檔案總管裡雙擊那個小檔案，
Windows會自動用預設的播放器（如Windows Media Player）打開播放，不需要自己找時間點、
不需要學怎麼用專業播放軟體。

每個片段會剪兩個版本：
  - 「精準版」：完全照chunk_audio.js的startTime/endTime，用來檢查掐頭去尾準不準
  - 「前後各留0.8秒版」：前後多留一點緩衝，聽起來比較自然，方便判斷「這段話聽起來對不對」

用法（不需要whisperx_env，一般3.14環境即可，但需要系統裝有ffmpeg並且能在命令列直接打
ffmpeg有反應；WhisperX環境本身就需要ffmpeg，通常代表你電腦上已經有了）：
  python extract_chunk_clips.py                  → 剪內建推薦清單（119/117/23篇代表性語塊 + 12條寬鬆比對）
  python extract_chunk_clips.py PSA119            → 剪某一整卷某一章全部語塊，例如詩篇119篇
  python extract_chunk_clips.py CK-EN-PSA023-02   → 剪單一指定語塊
"""
import os, re, json, subprocess, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHUNK_AUDIO_JS = os.path.join(BASE_DIR, "chunk_audio.js")
AUDIO_DIR = os.path.join(BASE_DIR, "bible_data", "audio", "en")
OUTPUT_DIR = os.path.join(BASE_DIR, "chunk_audio_preview")
PADDING = 0.8  # 「前後留白版」每邊多留的秒數

# 預設推薦抽查清單：涵蓋最長篇(119)、最短篇(117)、已知基準(23)，加上全部12條寬鬆比對案例
DEFAULT_CHUNK_IDS = [
    # 119篇（最長，抽幾條代表性的）
    "CK-EN-PSA119-01", "CK-EN-PSA119-05", "CK-EN-PSA119-13",
    # 117篇（最短）
    # 23篇（基準對照）
    "CK-EN-PSA023-01", "CK-EN-PSA023-02", "CK-EN-PSA023-03", "CK-EN-PSA023-04",
    # 12條不連續片語/寬鬆比對，全部納入抽查
    "CK-EN-PSA029-02", "CK-EN-PSA033-05", "CK-EN-PSA072-01", "CK-EN-PSA075-03",
    "CK-EN-PSA076-01", "CK-EN-PSA089-03", "CK-EN-PSA091-03", "CK-EN-PSA094-03",
    "CK-EN-PSA113-01", "CK-EN-PSA118-06", "CK-EN-PSA119-05", "CK-EN-PSA146-02",
]


def load_chunk_audio():
    with open(CHUNK_AUDIO_JS, encoding="utf-8") as f:
        text = f.read()
    idx = text.index("CHUNK_AUDIO")
    brace_start = text.index("{", idx)
    obj, _ = json.JSONDecoder().raw_decode(text, brace_start)
    return obj


def safe_filename(s, max_len=40):
    s = re.sub(r'[\\/:*?"<>|]', "", s)  # 去掉Windows檔名不允許的符號
    s = s.strip().replace(" ", "_")
    return s[:max_len]


def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


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
    if not check_ffmpeg():
        print("!! 找不到ffmpeg。請確認：")
        print("   1. 你電腦上WhisperX用的ffmpeg是否有加進系統PATH（不只是whisperx_env裡）")
        print("   2. 或直接在命令列打 ffmpeg -version 看看有沒有反應")
        print("   如果只有whisperx_env裡有ffmpeg，先執行 whisperx_env\\Scripts\\activate 再跑本腳本即可")
        return

    chunk_audio = load_chunk_audio()

    args = sys.argv[1:]
    if not args:
        target_ids = DEFAULT_CHUNK_IDS
        print(f"未指定範圍，使用內建推薦抽查清單（{len(target_ids)}條：119篇代表性語塊+23篇全部4條+12條寬鬆比對案例）")
    elif len(args) == 1 and args[0].startswith("CK-"):
        target_ids = [args[0]]
    else:
        book_or_chapter = args[0].upper()  # 例如 PSA119
        m = re.match(r'^([A-Z]{3})(\d+)$', book_or_chapter)
        if m:
            book, chapter = m.group(1), int(m.group(2))
            target_ids = [cid for cid, v in chunk_audio.items() if v["book"] == book and v["chapter"] == chapter]
            print(f"指定 {book} 第{chapter}章，共找到{len(target_ids)}條語塊")
        else:
            print(f"看不懂參數「{args[0]}」，請用語塊ID（如CK-EN-PSA023-02）或書卷+章節（如PSA119）")
            return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ok_count = fail_count = 0

    for cid in target_ids:
        info = chunk_audio.get(cid)
        if not info:
            print(f"  !! {cid}：在chunk_audio.js裡找不到這個ID，跳過")
            fail_count += 1
            continue
        audio_file = os.path.join(AUDIO_DIR, info["book"], info["audioFile"])
        if not os.path.exists(audio_file):
            print(f"  !! {cid}：找不到音頻檔案 {audio_file}，跳過")
            fail_count += 1
            continue

        label = f'{info["book"]}{info["chapter"]:03d}v{info["verse"]}_{safe_filename(info["matchedText"])}'
        exact_path = os.path.join(OUTPUT_DIR, f"{cid}_{label}_精準版.mp3")
        padded_path = os.path.join(OUTPUT_DIR, f"{cid}_{label}_留白版.mp3")

        ok1, err1 = extract_clip(audio_file, info["startTime"], info["endTime"], exact_path, padding=0)
        ok2, err2 = extract_clip(audio_file, info["startTime"], info["endTime"], padded_path, padding=PADDING)

        if ok1 and ok2:
            print(f"  ✓ {cid}（{info['matchedText']}）")
            ok_count += 1
        else:
            print(f"  !! {cid} 剪輯失敗：{err1 or err2}")
            fail_count += 1

    print(f"\n完成：{ok_count}條成功剪輯，{fail_count}條失敗")
    print(f"檔案存在：{OUTPUT_DIR}")
    print("每條語塊有兩個檔案：")
    print("  「_精準版」= 完全照chunk_audio.js算出來的起訖時間，用來檢查掐頭去尾準不準")
    print("  「_留白版」= 前後各多留0.8秒，聽起來比較自然完整，方便判斷整體對不對")
    print("直接在檔案總管裡雙擊任一個mp3檔案，就會用預設播放器打開播放。")


if __name__ == "__main__":
    main()
